import logging
from datetime import timedelta
from typing import Any, Mapping

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_EMAIL, CONF_PASSWORD
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

    intelligentcoordinator = OctopusIntelligentCoordinator(hass, email, password)
    await intelligentcoordinator.async_config_entry_first_refresh()

    _LOGGER.info(f"📊 Datos obtenidos en el coordinador: {intelligentcoordinator.data}")

    accounts = intelligentcoordinator.data.keys()
    for account in accounts:
        _LOGGER.info(f"📡 Creando selectores para la cuenta {account}")
        selects.append(OctopusChargeSchedule(account, intelligentcoordinator, len(accounts) == 1))

    if selects:
        async_add_entities(selects)
        _LOGGER.info(f"✅ Se han añadido {len(selects)} selectores")
    else:
        _LOGGER.warning("⚠️ No se ha añadido ningún selector")


class OctopusChargeSchedule(CoordinatorEntity, SelectEntity):
    """Entidad para seleccionar horarios de carga."""

    def __init__(self, account: str, coordinator, single: bool):
        super().__init__(coordinator)
        self._account = account
        self._attr_name = "Horario de carga" if single else f"Horario de carga ({account})"
        self._attr_unique_id = f"octopus_charge_schedule_{account}"
        self._attr_options = ["06:00", "07:00", "08:00", "09:00", "10:00"]  # Opciones de horario
        self._current_schedule = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    def _handle_coordinator_update(self) -> None:
        """Actualiza el estado con los datos de carga."""
        schedules = self.coordinator.data[self._account].get("preferences", {}).get("schedules", [])
        if schedules:
            first_schedule = schedules[0]  # Tomamos el primero como referencia
            self._current_schedule = first_schedule["time"]
        self.async_write_ha_state()

    @property
    def current_option(self) -> str | None:
        """Devuelve la opción actualmente seleccionada."""
        return self._current_schedule

    async def async_select_option(self, option: str) -> None:
        """Actualiza el horario de carga en la API."""
        _LOGGER.info(f"🔄 Actualizando horario de carga a {option} para la cuenta {self._account}")

        # Simulación de una llamada a la API para actualizar la configuración
        success = await self.coordinator._api.setVehicleChargePreferences(
            accountNumber=self._account,
            weekdayTargetSoc=85,  # Fijo en 85% por ahora
            weekendTargetSoc=85,
            weekdayTargetTime=option,
            weekendTargetTime=option,
        )

        if success:
            self._current_schedule = option
            self.async_write_ha_state()
        else:
            _LOGGER.error(f"❌ No se pudo actualizar el horario de carga para {self._account}")
