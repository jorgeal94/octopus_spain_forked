import logging
from datetime import timedelta
from typing import List
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant, callback
from .const import INTELLIGENT_SOC_OPTIONS, INTELLIGENT_CHARGE_TIMES, DAYS_OF_WEEK
from .octopus_spain import OctopusSpain
from homeassistant.config_entries import ConfigEntry

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
        for day in DAYS_OF_WEEK:
            select_entities.append(OctopusIntelligentTargetSoc(vehicle_coordinator, account, day))
            select_entities.append(OctopusIntelligentTargetTime(vehicle_coordinator, account, day))

    async_add_entities(select_entities)


class OctopusIntelligentGo(DataUpdateCoordinator):
    """Coordinador específico para la gestión de carga del vehículo."""
    
    def __init__(self, hass: HomeAssistant, email: str, password: str):
        super().__init__(hass=hass, logger=_LOGGER, name="Octopus Intelligent Go", update_interval=timedelta(minutes=1))
        self._api = OctopusSpain(email, password)
        self._data = {}

    async def _async_update_data(self):
        if await self._api.login():
            self._data = {}
            accounts = await self._api.accounts()
            for account in accounts:
                krakenflex_device = await self._api.devices(account)
                #vehicle_prefs = await self._api.get_vehicle_charging_preferences(account)
                self._data[account] = {
                    "krakenflex_device": krakenflex_device,
                }
        return self._data

    async def set_device_preferences(self, account_id: str, day_of_week: str, soc: int, time: str):
        """Actualiza las preferencias del dispositivo."""
        if await self._api.login():
            device_id = self._data[account_id]["krakenflex_device"]["id"]
            schedules = [{"dayOfWeek": day_of_week.upper(), "max": soc, "time": time}]
            
            success = await self._api.set_device_preferences(
                account_id=account_id,
                device_id=device_id,
                mode="CHARGE",
                schedules=schedules,
                unit="PERCENTAGE"
            )

            if success:
                self._data[account_id]["vehicle_charging_prefs"][day_of_week] = {
                    "max": soc,
                    "time": time
                }
                self.async_update_listeners()
                return True
        return False


class OctopusIntelligentTargetSoc(CoordinatorEntity, SelectEntity):
    """Selector de porcentaje de carga para cada día de la semana."""

    def __init__(self, coordinator: OctopusIntelligentGo, account_number: str, day_of_week: str):
        super().__init__(coordinator)
        self._account_number = account_number
        self._day_of_week = day_of_week
        self._unique_id = f"octopus_target_soc_{account_number}_{day_of_week}"
        self._attr_name = f"Octopus SOC {day_of_week} ({account_number})"
        self._options = INTELLIGENT_SOC_OPTIONS

        preferences = self.coordinator.data.get(self._account_number, {}).get("vehicle_charging_prefs", {})
        self._current_option = str(preferences.get(day_of_week, {}).get("max", 80))

    @property
    def current_option(self) -> str:
        return self._current_option

    @property
    def options(self) -> List[str]:
        return self._options

    async def async_select_option(self, option: str) -> None:
        """Cambia el SOC objetivo para el día específico."""
        time = self.coordinator.data.get(self._account_number, {}).get("vehicle_charging_prefs", {}).get(self._day_of_week, {}).get("time", "08:00")

        success = await self.coordinator.set_device_preferences(
            self._account_number,
            self._day_of_week,
            int(option),
            time
        )

        if success:
            self._current_option = option
            self.async_write_ha_state()


class OctopusIntelligentTargetTime(CoordinatorEntity, SelectEntity):
    """Selector de hora de carga para cada día de la semana."""

    def __init__(self, coordinator: OctopusIntelligentGo, account_number: str, day_of_week: str):
        super().__init__(coordinator)
        self._account_number = account_number
        self._day_of_week = day_of_week
        self._unique_id = f"octopus_target_time_{account_number}_{day_of_week}"
        self._attr_name = f"Octopus Charge Time {day_of_week} ({account_number})"
        self._options = INTELLIGENT_CHARGE_TIMES

        preferences = self.coordinator.data.get(self._account_number, {}).get("vehicle_charging_prefs", {})
        self._current_option = preferences.get(day_of_week, {}).get("time", "08:00")

    @property
    def current_option(self) -> str:
        return self._current_option

    @property
    def options(self) -> List[str]:
        return self._options

    async def async_select_option(self, option: str) -> None:
        """Cambia la hora de carga para el día específico."""
        soc = self.coordinator.data.get(self._account_number, {}).get("vehicle_charging_prefs", {}).get(self._day_of_week, {}).get("max", 80)

        success = await self.coordinator.set_device_preferences(
            self._account_number,
            self._day_of_week,
            soc,
            option
        )

        if success:
            self._current_option = option
            self.async_write_ha_state()