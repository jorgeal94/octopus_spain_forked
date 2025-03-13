import logging
from typing import List

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

    coordinator = OctopusCoordinator(hass, email, password)
    await coordinator.async_config_entry_first_refresh()

    select_entities = [
        OctopusIntelligentTargetSoc(coordinator),
        OctopusIntelligentTargetTime(coordinator),
    ]
    
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

class OctopusIntelligentTargetSoc(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator: OctopusCoordinator):
        super().__init__(coordinator=coordinator)
        self._unique_id = "octopus_intelligent_target_soc"
        self._name = "Octopus Target State of Charge"
        self._coordinator = coordinator
        self._current_option = None
        self._options = INTELLIGENT_SOC_OPTIONS

    @callback
    def _handle_coordinator_update(self):
        """Handle updated data from the coordinator."""
        target_soc = self._coordinator.data.get("octopus_system", {}).get("target_soc")
        if target_soc is not None:
            self._current_option = str(target_soc)
        self.async_write_ha_state()

    @property
    def current_option(self) -> str:
        """Return the current selected option."""
        return self._current_option

    @property
    def options(self) -> List[str]:
        """Return the available options."""
        return self._options

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    async def async_select_option(self, option: str) -> None:
        """Handle option selection."""
        await self._coordinator._api.set_target_soc(int(option))
        self._current_option = option
        self.async_write_ha_state()

class OctopusIntelligentTargetTime(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator: OctopusCoordinator):
        super().__init__(coordinator=coordinator)
        self._unique_id = "octopus_intelligent_target_time"
        self._name = "Octopus Target Ready By Time"
        self._coordinator = coordinator
        self._current_option = None
        self._options = INTELLIGENT_CHARGE_TIMES

    @callback
    def _handle_coordinator_update(self):
        """Handle updated data from the coordinator."""
        target_time = self._coordinator.data.get("octopus_system", {}).get("target_time")
        if target_time is not None:
            self._current_option = target_time
        self.async_write_ha_state()

    @property
    def current_option(self) -> str:
        """Return the current selected option."""
        return self._current_option

    @property
    def options(self) -> List[str]:
        """Return the available options."""
        return self._options

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    async def async_select_option(self, option: str) -> None:
        """Handle option selection."""
        await self._coordinator._api.set_target_time(option)
        self._current_option = option
        self.async_write_ha_state()
