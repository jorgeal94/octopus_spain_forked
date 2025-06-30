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

    if DOMAIN not in hass.data or "intelligent_coordinator" not in hass.data[DOMAIN]:
        _LOGGER.error("❌ intelligent_coordinator no está disponible en hass.data")
        return

    intelligentcoordinator = hass.data[DOMAIN]["intelligent_coordinator"]
    await intelligentcoordinator.async_config_entry_first_refresh()

    _LOGGER.info(f"📊 Datos obtenidos en el coordinador: {intelligentcoordinator.data}")

    selects = []
    accounts = intelligentcoordinator.data.keys()
    for account in accounts:
        _LOGGER.info(f"📡 Creando selectores para la cuenta {account}")
        devices = intelligentcoordinator.data[account].get("devices", [])
        if devices:
            for day in DAY_TRANSLATION.keys():
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
        self._attr_options = sorted(list(set([f"{h:02d}:30" for h in range(24)] + [f"{h:02d}:00" for h in range(24)])))
        self._current_time = "08:00"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    def _handle_coordinator_update(self) -> None:
        """Obtiene el horario actual desde el coordinador o establece un valor por defecto."""
        schedule_for_day = None
        devices = self.coordinator.data.get(self._account, {}).get("devices", [])
        if devices:
            schedules = devices[0].get("preferences", {}).get("schedules", [])
            if schedules:
                schedule_for_day = next((sched for sched in schedules if sched["dayOfWeek"] == self._day), None)

        if schedule_for_day and schedule_for_day.get("time"):
            # --- CAMBIO CLAVE AQUÍ ---
            # Recortamos los segundos (ej: "07:00:00" -> "07:00")
            self._current_time = schedule_for_day["time"][:5]
        else:
            self._current_time = "08:00"
        self.async_write_ha_state()
        
    @property
    def current_option(self) -> str | None:
        return self._current_time

    async def async_select_option(self, option: str) -> None:
        await self._update_charge_preferences(time=option)
        await self.coordinator.async_request_refresh()
    
    async def _update_charge_preferences(self, time: str = None, max_soc: int = None) -> None:
        devices = self.coordinator.data.get(self._account, {}).get("devices", [])
        if not devices:
            _LOGGER.error("❌ No se encontraron dispositivos.")
            return

        device_id = devices[0].get("id")
        current_schedules = devices[0].get("preferences", {}).get("schedules", [])
        schedules = []
        for day in DAY_TRANSLATION.keys():
            current_schedule_for_day = next((sched for sched in current_schedules if sched["dayOfWeek"] == day), None)
            
            day_time = time if day == self._day and time is not None else (current_schedule_for_day['time'][:5] if current_schedule_for_day else "08:00")
            day_soc = max_soc if day == self._day and max_soc is not None else (current_schedule_for_day['max'] if current_schedule_for_day else 80)

            schedules.append({"dayOfWeek": day, "time": day_time, "max": str(day_soc)})

        await self.coordinator._api.set_device_preferences(
            device_id=device_id, mode="CHARGE", unit="PERCENTAGE", schedules=schedules
        )


class OctopusChargeSoc1(CoordinatorEntity, SelectEntity):
    """Selector para elegir el SOC máximo por día de la semana."""

    def __init__(self, account: str, coordinator, day: str):
        super().__init__(coordinator)
        self._account = account
        self._day = day.upper()
        self._attr_name = f"SOC de carga {DAY_TRANSLATION.get(self._day, self._day)}"
        self._attr_unique_id = f"octopus_charge_soc_{account}_{day.lower()}"
        self._attr_options = [str(i) for i in range(20, 101, 5)]
        self._current_soc = "80"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    def _handle_coordinator_update(self) -> None:
        """Obtiene el SOC actual desde el coordinador o establece un valor por defecto."""
        schedule_for_day = None
        devices = self.coordinator.data.get(self._account, {}).get("devices", [])
        if devices:
            schedules = devices[0].get("preferences", {}).get("schedules", [])
            if schedules:
                schedule_for_day = next((sched for sched in schedules if sched["dayOfWeek"] == self._day), None)
        
        if schedule_for_day and schedule_for_day.get("max") is not None:
            # --- CAMBIO CLAVE AQUÍ ---
            # Nos aseguramos de que sea un entero y luego un string (ej: 80.0 -> "80")
            self._current_soc = str(int(float(schedule_for_day["max"])))
        else:
            self._current_soc = "80"
        self.async_write_ha_state()

    @property
    def current_option(self) -> str | None:
        return str(self._current_soc) if self._current_soc is not None else None

    async def async_select_option(self, option: str) -> None:
        await self._update_charge_preferences(max_soc=int(option))
        await self.coordinator.async_request_refresh()
    
    async def _update_charge_preferences(self, time: str = None, max_soc: int = None) -> None:
        devices = self.coordinator.data.get(self._account, {}).get("devices", [])
        if not devices:
            _LOGGER.error("❌ No se encontraron dispositivos.")
            return

        device_id = devices[0].get("id")
        current_schedules = devices[0].get("preferences", {}).get("schedules", [])
        schedules = []
        for day in DAY_TRANSLATION.keys():
            current_schedule_for_day = next((sched for sched in current_schedules if sched["dayOfWeek"] == day), None)
            
            day_time = time if day == self._day and time is not None else (current_schedule_for_day['time'][:5] if current_schedule_for_day else "08:00")
            day_soc = max_soc if day == self._day and max_soc is not None else (current_schedule_for_day['max'] if current_schedule_for_day else 80)

            schedules.append({"dayOfWeek": day, "time": day_time, "max": str(day_soc)})

        await self.coordinator._api.set_device_preferences(
            device_id=device_id, mode="CHARGE", unit="PERCENTAGE", schedules=schedules
        )
        