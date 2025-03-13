import logging
from typing import List

from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity  # Asegúrate de tener esta importación
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant, callback
from .const import INTELLIGENT_SOC_OPTIONS, INTELLIGENT_CHARGE_TIMES
from .lib.octopus_spain import OctopusSpain
from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, 
    entry: ConfigEntry, 
    async_add_entities: AddEntitiesCallback
) -> None:
    email = entry.data["email"]
    password = entry.data["password"]

    main_coordinator = OctopusCoordinator(hass, email, password)
    await main_coordinator.async_config_entry_first_refresh()

    select_entities = []
    for account in main_coordinator.data:
        vehicle_coordinator = OctopusIntelligentGo(hass, main_coordinator._api, account)
        await vehicle_coordinator.async_config_entry_first_refresh()
        
        select_entities.append(OctopusIntelligentTargetSoc(vehicle_coordinator))
        select_entities.append(OctopusIntelligentTargetTime(vehicle_coordinator))

    async_add_entities(select_entities)

class OctopusCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, email: str, password: str):
        super().__init__(hass=hass, logger=_LOGGER, name="Octopus Spain", update_interval=timedelta(hours=1))
        self._api = OctopusSpain(email, password)
        self._data = {}

    async def _async_update_data(self):
        if await self._api.login():
            self._data = {}
            accounts = await self._api.accounts()
            for account in accounts:
                account_data = await self._api.account(account)
                krakenflex_device = await self._api.registered_krakenflex_device(account)
                self._data[account] = {
                    **account_data,
                    "krakenflex_device": krakenflex_device
                }
        return self._data

class OctopusIntelligentGo(DataUpdateCoordinator):
    """Coordinador específico para gestionar las preferencias de carga inteligente del vehículo."""
    
    def __init__(self, hass: HomeAssistant, api: OctopusSpain, account_id: str):
        """Inicializa el coordinador."""
        super().__init__(hass, _LOGGER, name=f"Octopus Intelligent Go ({account_id})", update_interval=timedelta(minutes=1))
        self._api = api
        self._account_id = account_id
        self._data = {}

    async def _async_update_data(self):
        """Obtiene las preferencias de carga desde la API GraphQL."""
        return await self._api.get_vehicle_charging_preferences(self._account_id)

    async def set_target_soc(self, target_soc: int):
        """Actualiza el SOC objetivo en la API."""
        await self._api.set_target_soc(self._account_id, target_soc)
        await self.async_request_refresh()  # Refresca los datos tras la actualización

    async def set_target_time(self, target_time: str):
        """Actualiza la hora de carga objetivo en la API."""
        await self._api.set_target_time(self._account_id, target_time)
        await self.async_request_refresh()  # Refresca los datos tras la actualización

class OctopusIntelligentTargetSoc(CoordinatorEntity, SelectEntity):
    """Entidad para gestionar el estado de carga objetivo (SOC) en Octopus Intelligent Go."""
    
    def __init__(self, coordinator: OctopusIntelligentGo):
        super().__init__(coordinator)
        self._unique_id = f"octopus_target_soc_{coordinator._account_id}"
        self._name = f"Octopus Target SOC ({coordinator._account_id})"
        self._coordinator = coordinator
        self._current_option = None
        self._options = INTELLIGENT_SOC_OPTIONS

    @callback
    def _handle_coordinator_update(self):
        """Actualiza el estado cuando hay nuevos datos en el coordinador."""
        self._current_option = str(self._coordinator.data.get("weekdayTargetSoc", 80))  # Default: 80%
        self.async_write_ha_state()

    @property
    def current_option(self) -> str:
        return self._current_option

    @property
    def options(self) -> List[str]:
        return self._options

    async def async_select_option(self, option: str) -> None:
        """Cambia el valor del SOC objetivo."""
        await self._coordinator.set_target_soc(int(option))
        self._current_option = option
        self.async_write_ha_state()

class OctopusIntelligentTargetTime(CoordinatorEntity, SelectEntity):
    """Entidad para gestionar la hora de carga objetivo en Octopus Intelligent Go."""
    
    def __init__(self, coordinator: OctopusIntelligentGo):
        super().__init__(coordinator)
        self._unique_id = f"octopus_target_time_{coordinator._account_id}"
        self._name = f"Octopus Target Time ({coordinator._account_id})"
        self._coordinator = coordinator
        self._current_option = None
        self._options = INTELLIGENT_CHARGE_TIMES

    @callback
    def _handle_coordinator_update(self):
        """Actualiza el estado cuando hay nuevos datos en el coordinador."""
        self._current_option = self._coordinator.data.get("weekdayTargetTime", "08:00")  # Default: 08:00
        self.async_write_ha_state()

    @property
    def current_option(self) -> str:
        return self._current_option

    @property
    def options(self) -> List[str]:
        return self._options

    async def async_select_option(self, option: str) -> None:
        """Cambia el valor de la hora objetivo de carga."""
        await self._coordinator.set_target_time(option)
        self._current_option = option
        self.async_write_ha_state()

