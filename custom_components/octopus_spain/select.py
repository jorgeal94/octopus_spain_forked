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
        selects.append(OctopusChargeSoc(account, intelligentcoordinator, 0))
        selects.append(OctopusChargeSoc(account, intelligentcoordinator, 1))
        #selects.append(WeekdayOctopusChargeSoc(account, intelligentcoordinator, len(accounts) == 1))
        #selects.append(WeekendOctopusChargeSoc(account, intelligentcoordinator, len(accounts) == 1))

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
            account_number=self._account,
            weekday_soc=85,  # Fijo en 85% por ahora
            weekend_soc=85,
            weekday_time=option,
            weekend_time=option,
        )

        if success:
            self._current_schedule = option
            self.async_write_ha_state()
        else:
            _LOGGER.error(f"❌ No se pudo actualizar el horario de carga para {self._account}")

class OctopusChargeSoc(CoordinatorEntity, SelectEntity):
    """Entidad para seleccionar el SOC de carga del vehículo."""

    def __init__(self, account: str, coordinator, is_weekend: bool = False):
        super().__init__(coordinator)
        self._account = account
        self._is_weekend = is_weekend
        self._attr_name = "SOC de carga" if not is_weekend else f"SOC de carga (Fin de semana) ({account})"
        self._attr_unique_id = f"octopus_charge_soc_{account}_weekend" if is_weekend else f"octopus_charge_soc_{account}"
        self._attr_options = [str(i) for i in range(0, 101, 5)]  # Opciones de SOC de 0 a 100, en pasos de 5
        self._current_soc = None

    async def async_added_to_hass(self) -> None:
        """Actualiza el estado de la entidad cuando se agrega a Home Assistant."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    def _handle_coordinator_update(self) -> None:
        """Actualiza el estado con los datos de carga del SOC."""
        preferences = self.coordinator.data.get(self._account, {}).get("preferences", {})
        if preferences:
            if self._is_weekend:
                self._current_soc = preferences.get("weekendTargetSoc", None)
            else:
                self._current_soc = preferences.get("weekdayTargetSoc", None)
        self.async_write_ha_state()

    @property
    def current_option(self) -> str | None:
        """Devuelve el SOC actualmente seleccionado."""
        return str(self._current_soc) if self._current_soc is not None else None

    async def async_select_option(self, option: str) -> None:
        """Actualiza el SOC de carga en la API de Octopus."""
        _LOGGER.info(f"🔄 Actualizando SOC de carga a {option}% para la cuenta {self._account}")

        # Llamada a la API para actualizar las preferencias de carga
        success = await self.coordinator._api.setVehicleChargePreferences(
            account_number=self._account,
            weekday_soc=int(option) if not self._is_weekend else 85,  # Fijo a 85% para fines de semana
            weekend_soc=int(option) if self._is_weekend else 85,  # Fijo a 85% para días de semana
            weekday_time="09:00",  # Hora fija de carga
            weekend_time="09:00",  # Hora fija de carga
        )

        if success:
            self._current_soc = int(option)
            self.async_write_ha_state()
        else:
            _LOGGER.error(f"❌ No se pudo actualizar el SOC de carga para {self._account}")

class WeekdayOctopusChargeSoc(CoordinatorEntity, SelectEntity):
    """Entidad para seleccionar el SOC de carga del vehículo (Días de semana)."""

    def __init__(self, account: str, coordinator):
        super().__init__(coordinator)
        self._account = account
        self._attr_name = f"SOC de carga (Días de semana) ({account})"
        self._attr_unique_id = f"octopus_charge_soc_weekday_{account}"
        self._attr_options = [str(i) for i in range(0, 101, 5)]  # Opciones de SOC de 0 a 100, en pasos de 5
        self._current_soc = None

    async def async_added_to_hass(self) -> None:
        """Actualiza el estado de la entidad cuando se agrega a Home Assistant."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    def _handle_coordinator_update(self) -> None:
        """Actualiza el estado con los datos de carga del SOC para días de semana."""
        preferences = self.coordinator.data.get(self._account, {}).get("preferences", {})
        if preferences:
            self._current_soc = preferences.get("weekdayTargetSoc", None)
        self.async_write_ha_state()

    @property
    def current_option(self) -> str | None:
        """Devuelve el SOC actualmente seleccionado para los días de semana."""
        return str(self._current_soc) if self._current_soc is not None else None

    async def async_select_option(self, option: str) -> None:
        """Actualiza el SOC de carga en la API de Octopus para los días de semana."""
        _LOGGER.info(f"🔄 Actualizando SOC de carga a {option}% para la cuenta {self._account} (Días de semana)")

        # Llamada a la API para actualizar las preferencias de carga para días de semana
        success = await self.coordinator._api.setVehicleChargePreferences(
            account_number=self._account,
            weekday_soc=int(option),  # Cambiar el SOC para los días de semana
            weekend_soc=85,  # Fijo a 85% para fines de semana
            weekday_time="09:00",  # Hora fija de carga
            weekend_time="09:00",  # Hora fija de carga
        )

        if success:
            self._current_soc = int(option)
            self.async_write_ha_state()
        else:
            _LOGGER.error(f"❌ No se pudo actualizar el SOC de carga para {self._account} (Días de semana)")

class WeekendOctopusChargeSoc(CoordinatorEntity, SelectEntity):
    """Entidad para seleccionar el SOC de carga del vehículo (Fin de semana)."""

    def __init__(self, account: str, coordinator):
        super().__init__(coordinator)
        self._account = account
        self._attr_name = f"SOC de carga (Fin de semana) ({account})"
        self._attr_unique_id = f"octopus_charge_soc_weekend_{account}"
        self._attr_options = [str(i) for i in range(0, 101, 5)]  # Opciones de SOC de 0 a 100, en pasos de 5
        self._current_soc = None

    async def async_added_to_hass(self) -> None:
        """Actualiza el estado de la entidad cuando se agrega a Home Assistant."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    def _handle_coordinator_update(self) -> None:
        """Actualiza el estado con los datos de carga del SOC para fin de semana."""
        preferences = self.coordinator.data.get(self._account, {}).get("preferences", {})
        if preferences:
            self._current_soc = preferences.get("weekendTargetSoc", None)
        self.async_write_ha_state()

    @property
    def current_option(self) -> str | None:
        """Devuelve el SOC actualmente seleccionado para fin de semana."""
        return str(self._current_soc) if self._current_soc is not None else None

    async def async_select_option(self, option: str) -> None:
        """Actualiza el SOC de carga en la API de Octopus para fin de semana."""
        _LOGGER.info(f"🔄 Actualizando SOC de carga a {option}% para la cuenta {self._account} (Fin de semana)")

        # Llamada a la API para actualizar las preferencias de carga para fin de semana
        success = await self.coordinator._api.setVehicleChargePreferences(
            account_number=self._account,
            weekday_soc=85,  # Fijo a 85% para días de semana
            weekend_soc=int(option),  # Cambiar el SOC para el fin de semana
            weekday_time="09:00",  # Hora fija de carga
            weekend_time="09:00",  # Hora fija de carga
        )

        if success:
            self._current_soc = int(option)
            self.async_write_ha_state()
        else:
            _LOGGER.error(f"❌ No se pudo actualizar el SOC de carga para {self._account} (Fin de semana)")

