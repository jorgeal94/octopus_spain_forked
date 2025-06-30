import logging
from datetime import timedelta
from typing import Any, Mapping

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN
from .coordinator import OctopusIntelligentCoordinator

_LOGGER = logging.getLogger(__name__)

DAY_TRANSLATION = {
    "MONDAY": "Lunes",
    "TUESDAY": "Martes",
    "WEDNESDAY": "Miércoles",
    "THURSDAY": "Jueves",
    "FRIDAY": "Viernes",
    "SATURDAY": "Sábado",
    "SUNDAY": "Domingo",
}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Configurar selectores para Octopus Spain."""
    _LOGGER.info("🛠️ Configurando selectores de Octopus Spain")

    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]

    selects = []

    if DOMAIN not in hass.data or "intelligent_coordinator" not in hass.data[DOMAIN]:
        _LOGGER.error("❌ intelligent_coordinator no está disponible en hass.data")
        return

    intelligentcoordinator = hass.data[DOMAIN]["intelligent_coordinator"]
    await intelligentcoordinator.async_config_entry_first_refresh()

    _LOGGER.info(f"📊 Datos obtenidos en el coordinador: {intelligentcoordinator.data}")

    accounts = intelligentcoordinator.data.keys()
    for account in accounts:
        _LOGGER.info(f"📡 Creando selectores para la cuenta {account}")
        devices = intelligentcoordinator.data[account].get("devices", [])
        if devices:
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                selects.append(OctopusChargeTime1(account, intelligentcoordinator, day))
                selects.append(OctopusChargeSoc1(account, intelligentcoordinator, day))

    if selects:
        async_add_entities(selects)
        _LOGGER.info(f"✅ Se han añadido {len(selects)} selectores")
    else:
        _LOGGER.warning("⚠️ No se ha añadido ningún selector")


class OctopusChargeTime1(CoordinatorEntity, SelectEntity):
    """Selector para elegir la hora de carga por día de la semana."""

    def __init__(self, account: str, coordinator, day: str):
        super().__init__(coordinator)
        self._account = account
        self._day = day.upper()
        self._attr_name = f"Hora de carga {DAY_TRANSLATION.get(self._day, self._day)}"
        self._attr_unique_id = f"octopus_charge_time_{account}_{day.lower()}"
        self._attr_options = [f"{h:02d}:30" for h in range(24)] + [f"{h:02d}:00" for h in range(24)]
        self._attr_options.sort()
        self._current_time = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    def _handle_coordinator_update(self) -> None:
        """Obtiene el horario actual desde la API."""
        devices = self.coordinator.data.get(self._account, {}).get("devices", [])
        if devices:
            schedules = devices[0].get("preferences", {}).get("schedules", [])
            for schedule in schedules:
                if schedule["dayOfWeek"] == self._day:
                    self._current_time = schedule["time"]
        self.async_write_ha_state()
        
    @property
    def current_option(self) -> str | None:
        return self._current_time

    async def async_select_option(self, option: str) -> None:
        """Actualiza la hora de carga y llama a la API."""
        _LOGGER.info(f"🔄 Actualizando hora de carga para {self._day}: {option}")
        await self._update_charge_preferences(time=option)
        await self.coordinator.async_request_refresh()
    
    async def _update_charge_preferences(self, time: str = None, max_soc: int = None) -> None:
        """Llama a la API para actualizar los valores de carga."""
        devices = self.coordinator.data.get(self._account, {}).get("devices", [])
        if not devices:
            _LOGGER.error("❌ No se encontraron dispositivos en los datos del coordinador.")
            return

        device_id = devices[0].get("id")
        if not device_id:
            _LOGGER.error("❌ No se encontró un ID de dispositivo válido.")
            return

        current_schedules = devices[0].get("preferences", {}).get("schedules", [])
        schedules = []
        for day in DAY_TRANSLATION.keys():
            current_schedule_for_day = next((sched for sched in current_schedules if sched["dayOfWeek"] == day), None)
            
            day_time = time if day == self._day and time is not None else (current_schedule_for_day['time'] if current_schedule_for_day else "08:00:00")
            day_soc = max_soc if day == self._day and max_soc is not None else (current_schedule_for_day['max'] if current_schedule_for_day else 80)

            schedules.append({"dayOfWeek": day, "time": day_time, "max": day_soc})

        success = await self.coordinator._api.set_device_preferences(
            device_id=device_id, mode="CHARGE", unit="PERCENTAGE", schedules=schedules
        )

        if success:
            if time is not None:
                self._current_time = time
            self.async_write_ha_state()
        else:
            _LOGGER.error(f"❌ No se pudo actualizar la hora de carga para {self._day}")


class OctopusChargeSoc1(CoordinatorEntity, SelectEntity):
    """Selector para elegir el SOC máximo por día de la semana."""

    def __init__(self, account: str, coordinator, day: str):
        super().__init__(coordinator)
        self._account = account
        self._day = day.upper()
        self._attr_name = f"SOC de carga {DAY_TRANSLATION.get(self._day, self._day)}"
        self._attr_unique_id = f"octopus_charge_soc_{account}_{day.lower()}"
        self._attr_options = [str(i) for i in range(20, 101, 5)]
        self._current_soc = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    def _handle_coordinator_update(self) -> None:
        """Obtiene el SOC actual desde la API."""
        devices = self.coordinator.data.get(self._account, {}).get("devices", [])
        if devices:
            schedules = devices[0].get("preferences", {}).get("schedules", [])
            for schedule in schedules:
                if schedule["dayOfWeek"] == self._day:
                    self._current_soc = schedule["max"]
        self.async_write_ha_state()

    @property
    def current_option(self) -> str | None:
        return str(self._current_soc) if self._current_soc is not None else None

    async def async_select_option(self, option: str) -> None:
        """Actualiza el SOC máximo y llama a la API."""
        _LOGGER.info(f"🔄 Actualizando SOC de carga para {self._day}: {option}%")
        await self._update_charge_preferences(max_soc=int(option))
        await self.coordinator.async_request_refresh()
    
    async def _update_charge_preferences(self, time: str = None, max_soc: int = None) -> None:
        """Llama a la API para actualizar los valores de carga."""
        devices = self.coordinator.data.get(self._account, {}).get("devices", [])
        if not devices:
            _LOGGER.error("❌ No se encontraron dispositivos en los datos del coordinador.")
            return

        device_id = devices[0].get("id")
        if not device_id:
            _LOGGER.error("❌ No se encontró un ID de dispositivo válido.")
            return
        
        current_schedules = devices[0].get("preferences", {}).get("schedules", [])
        schedules = []
        for day in DAY_TRANSLATION.keys():
            current_schedule_for_day = next((sched for sched in current_schedules if sched["dayOfWeek"] == day), None)
            
            day_time = time if day == self._day and time is not None else (current_schedule_for_day['time'] if current_schedule_for_day else "08:00:00")
            day_soc = max_soc if day == self._day and max_soc is not None else (current_schedule_for_day['max'] if current_schedule_for_day else 80)

            schedules.append({"dayOfWeek": day, "time": day_time, "max": day_soc})

        success = await self.coordinator._api.set_device_preferences(
            device_id=device_id, mode="CHARGE", unit="PERCENTAGE", schedules=schedules
        )

        if success:
            if max_soc is not None:
                self._current_soc = int(max_soc)
            self.async_write_ha_state()
        else:
            _LOGGER.error(f"❌ No se pudo actualizar el SOC de carga para {self._day}")