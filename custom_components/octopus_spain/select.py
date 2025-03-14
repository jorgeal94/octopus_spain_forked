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
from homeassistant.helpers.entity import DeviceInfo

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, 
    entry: ConfigEntry, 
    async_add_entities: AddEntitiesCallback
) -> None:
    email = entry.data["email"]
    password = entry.data["password"]

    vehicle_coordinator = OctopusIntelligentGo(hass, email, password)
    await vehicle_coordinator.async_config_entry_first_refresh()

    select_entities = []
    accounts = vehicle_coordinator.data.keys()
    for account in accounts:
        # Crear y agregar el selector de SOC para cada cuenta
        select_entities.append(OctopusIntelligentTargetSoc(vehicle_coordinator, account))

    async_add_entities(select_entities)
        

class OctopusIntelligentGo(DataUpdateCoordinator):
    """Coordinador específico para gestionar las preferencias de carga inteligente del vehículo."""
    def __init__(self, hass: HomeAssistant, email: str, password: str):
        super().__init__(hass=hass, logger=_LOGGER, name="Octopus Intelligent Go", update_interval=timedelta(minutes=1))
        self._api = OctopusSpain(email, password)
        self._data = {}

    async def _async_update_data(self):
        if await self._api.login():
            self._data = {}
            accounts = await self._api.accounts()
            for account in accounts:
                krakenflex_device = await self._api.registered_krakenflex_device(account)
                vehicle_prefs = await self._api.get_vehicle_charging_preferences(account)
                self._data[account] = {
                    "krakenflex_device": krakenflex_device,
                    "vehicle_charging_prefs": vehicle_prefs
                }

        return self._data
    
    async def set_target_soc(self, account_id: str, weekday_target_soc: int, weekend_target_soc: int, weekday_target_time: str, weekend_target_time: str):
        """Actualiza las preferencias de carga del vehículo en la API."""
        if await self._api.login():
            accounts = await self._api.accounts()
            for account in accounts:
                if account == account_id:
                    # Llamada a la API para actualizar las preferencias de carga
                    success = await self._api.set_targets(
                        account_id,
                        weekday_target_soc,
                        weekend_target_soc,
                        weekday_target_time,
                        weekend_target_time
                    )
                    if success:
                        # Actualiza los datos internos del coordinador con las nuevas preferencias
                        self._data[account_id]["vehicle_charging_prefs"] = {
                            "weekdayTargetSoc": weekday_target_soc,
                            "weekendTargetSoc": weekend_target_soc,
                            "weekdayTargetTime": weekday_target_time,
                            "weekendTargetTime": weekend_target_time
                        }
                        self.async_write_ha_state()
                        return True
        return False


class OctopusIntelligentTargetSoc(CoordinatorEntity, SelectEntity):
    """Entidad para gestionar el estado de carga objetivo (SOC) en Octopus Intelligent Go."""

    def __init__(self, coordinator: OctopusIntelligentGo, account_number: str):
        super().__init__(coordinator)
        self._account_number = account_number
        self._unique_id = f"octopus_target_soc_{account_number}"
        self._name = f"Octopus Target SOC ({account_number})"
        self._current_option = None
        self._options = INTELLIGENT_SOC_OPTIONS  # Define los valores posibles (e.g., 10%, 20%, ... 100%)
        self._current_weekday_target_soc = None
        self._current_weekend_target_soc = None
        self._current_weekday_target_time = None
        self._current_weekend_target_time = None

    @property
    def name(self) -> str:
        """Devuelve el nombre de la entidad."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Devuelve un identificador único para la entidad."""
        return self._unique_id

    @property
    def device_info(self) -> DeviceInfo:
        """Devuelve la información del dispositivo al que pertenece la entidad."""
        return DeviceInfo(
            identifiers={(self._account_number,)},
            name=f"Octopus Account {self._account_number}",
            manufacturer="Octopus Energy",
            model="Intelligent Go",
        )
    
    @callback
    def _handle_coordinator_update(self):
        """Actualiza el estado cuando hay nuevos datos en el coordinador."""
        preferences = self.coordinator.data.get(self._account_number, {}).get("vehicle_charging_prefs", {})
        if preferences:
            # Establecer el valor predeterminado con el valor actual del SOC objetivo
            self._current_weekday_target_soc = str(preferences.get("weekdayTargetSoc", 80))  # Valor predeterminado: 80%
            self._current_weekend_target_soc = str(preferences.get("weekendTargetSoc", 80))  # Valor predeterminado: 80%
            self._current_weekday_target_time = preferences.get("weekdayTargetTime", "08:00")  # Valor predeterminado: "08:00"
            self._current_weekend_target_time = preferences.get("weekendTargetTime", "08:00")  # Valor predeterminado: "08:00"
        self.async_write_ha_state()

    @property
    def current_option(self) -> str:
        return self._current_weekday_target_soc

    @property
    def options(self) -> List[str]:
        return self._options

    async def async_select_option(self, option: str) -> None:
        """Cambia el valor del SOC objetivo."""
        # Llamar a la API para actualizar los valores de carga objetivo
        weekday_target_soc = int(option)
        weekend_target_soc = self._current_weekend_target_soc
        weekday_target_time = self._current_weekday_target_time
        weekend_target_time = self._current_weekend_target_time

        success = await self.coordinator.set_target_soc(
            self._account_number,
            weekday_target_soc,
            weekend_target_soc,
            weekday_target_time,
            weekend_target_time
        )

        if success:
            self._current_weekday_target_soc = option
            self.async_write_ha_state()