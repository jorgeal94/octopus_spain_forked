import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
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
    intelligentcoordinator = hass.data[DOMAIN].get("intelligent_coordinator")
    if not intelligentcoordinator:
        return

    selects = []
    accounts = intelligentcoordinator.data.keys()
    for account in accounts:
        devices = intelligentcoordinator.data[account].get("devices", [])
        if devices:
            for day in DAY_TRANSLATION:
                selects.append(OctopusChargeTimeSelector(account, intelligentcoordinator, day))
                selects.append(OctopusChargeSocSelector(account, intelligentcoordinator, day))

    if selects:
        async_add_entities(selects)


class BaseOctopusChargeSelector(CoordinatorEntity, SelectEntity):
    """Clase base para los selectores de carga."""

    def __init__(self, account: str, coordinator: OctopusIntelligentCoordinator, day: str):
        super().__init__(coordinator)
        self._account = account
        self._day = day.upper()

    def _get_current_schedules(self) -> list[dict[str, Any]]:
        """Obtiene la lista completa de horarios del dispositivo."""
        devices = self.coordinator.data.get(self._account, {}).get("devices", [])
        if devices:
            return devices[0].get("preferences", {}).get("schedules", [])
        return []

    async def _update_charge_preferences(self, time: str | None = None, max_soc: int | None = None) -> None:
        """Construye y envía la configuración de horarios completa a la API."""
        devices = self.coordinator.data.get(self._account, {}).get("devices", [])
        if not (devices and (device_id := devices[0].get("id"))):
            _LOGGER.error("No se encontró un ID de dispositivo válido.")
            return

        current_schedules = self._get_current_schedules()
        new_schedules = []

        for day_key in DAY_TRANSLATION:
            # Busca el horario actual para este día en la lista completa
            current_schedule_for_day = next(
                (sched for sched in current_schedules if sched["dayOfWeek"] == day_key), None
            )

            # Determina el valor a usar: el nuevo si es el día que se modifica, si no el actual, y si no existe, el por defecto.
            day_time = time if day_key == self._day and time is not None else (current_schedule_for_day['time'][:5] if current_schedule_for_day else "08:00")
            day_soc_val = max_soc if day_key == self._day and max_soc is not None else (current_schedule_for_day['max'] if current_schedule_for_day else 80)

            new_schedules.append({"dayOfWeek": day_key, "time": day_time, "max": str(int(float(day_soc_val)))})

        await self.coordinator._api.set_device_preferences(
            device_id=device_id, mode="CHARGE", unit="PERCENTAGE", schedules=new_schedules
        )
        await self.coordinator.async_request_refresh()


class OctopusChargeTimeSelector(BaseOctopusChargeSelector):
    """Selector para la hora de carga diaria."""

    def __init__(self, account: str, coordinator: OctopusIntelligentCoordinator, day: str):
        super().__init__(account, coordinator, day)
        self._attr_name = f"Hora de carga {DAY_TRANSLATION.get(self._day, self._day)}"
        self._attr_unique_id = f"octopus_charge_time_{account}_{day.lower()}"
        self._attr_options = sorted([f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)])

    @property
    def current_option(self) -> str | None:
        """Devuelve la hora de carga actual."""
        current_schedules = self._get_current_schedules()
        schedule = next((sched for sched in current_schedules if sched["dayOfWeek"] == self._day), None)
        return schedule['time'][:5] if schedule else "08:00"

    async def async_select_option(self, option: str) -> None:
        """Actualiza la hora de carga."""
        await self._update_charge_preferences(time=option)


class OctopusChargeSocSelector(BaseOctopusChargeSelector):
    """Selector para el SOC máximo diario."""

    def __init__(self, account: str, coordinator: OctopusIntelligentCoordinator, day: str):
        super().__init__(account, coordinator, day)
        self._attr_name = f"SOC de carga {DAY_TRANSLATION.get(self._day, self._day)}"
        self._attr_unique_id = f"octopus_charge_soc_{account}_{day.lower()}"
        self._attr_options = [str(i) for i in range(20, 101, 5)]

    @property
    def current_option(self) -> str | None:
        """Devuelve el SOC máximo actual."""
        current_schedules = self._get_current_schedules()
        schedule = next((sched for sched in current_schedules if sched["dayOfWeek"] == self._day), None)
        return str(int(float(schedule['max']))) if schedule else "80"

    async def async_select_option(self, option: str) -> None:
        """Actualiza el SOC máximo."""
        await self._update_charge_preferences(max_soc=int(option))