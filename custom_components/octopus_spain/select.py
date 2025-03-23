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

    # ✅ Usa el coordinador ya creado en `__init__.py`  
    #intelligentcoordinator = hass.data["octopus_spain"]["intelligent_coordinator"]
    #await intelligentcoordinator.async_config_entry_first_refresh()
    # 🔹 Esperar a que el coordinador se inicialice en __init__.py
    if DOMAIN not in hass.data or "intelligent_coordinator" not in hass.data[DOMAIN]:
        _LOGGER.error("❌ intelligent_coordinator no está disponible en hass.data")
        return

    intelligentcoordinator = hass.data[DOMAIN]["intelligent_coordinator"]
    await intelligentcoordinator.async_config_entry_first_refresh()

    _LOGGER.info(f"📊 Datos obtenidos en el coordinador: {intelligentcoordinator.data}")

    accounts = intelligentcoordinator.data.keys()
    for account in accounts:
        _LOGGER.info(f"📡 Creando selectores para la cuenta {account}")
        selects.append(OctopusChargeSchedule(account, intelligentcoordinator, len(accounts) == 1))
        selects.append(OctopusChargeW(account, intelligentcoordinator, 0))
        selects.append(OctopusChargeW(account, intelligentcoordinator, 1))
        #selects.append(WeekdayOctopusChargeSoc(account, intelligentcoordinator, len(accounts) == 1))
        #selects.append(WeekendOctopusChargeSoc(account, intelligentcoordinator, len(accounts) == 1))
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            selects.append(OctopusChargeTime1(account, intelligentcoordinator, day))
            selects.append(OctopusChargeSoc1(account, intelligentcoordinator, day))

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
            weekday_soc=80,  # Fijo en 85% por ahora
            weekend_soc=80,
            weekday_time=option,
            weekend_time=option,
        )

        if success:
            self._current_schedule = option
            self.async_write_ha_state()
              # 🔄 FORZAR actualización del coordinador para que los sensores reflejen el cambio de inmediato
            await self.coordinator.async_request_refresh()

        else:
            _LOGGER.error(f"❌ No se pudo actualizar el horario de carga para {self._account}")

class OctopusChargeW(CoordinatorEntity, SelectEntity):
    """Entidad para seleccionar el SOC de carga del vehículo."""

    def __init__(self, account: str, coordinator, is_weekend: bool = False):
        super().__init__(coordinator)
        self._account = account
        self._is_weekend = is_weekend
        self._attr_name = f"SOC de carga ({account})" if not is_weekend else f"SOC de carga (Fin de semana) ({account})"
        self._attr_unique_id = f"octopus_charge_soc_{account}_weekend" if is_weekend else f"octopus_charge_soc_{account}"
        self._attr_options = [str(i) for i in range(0, 101, 5)]  # Opciones de SOC de 0 a 100, en pasos de 5
        self._current_soc = None

    async def async_added_to_hass(self) -> None:
        """Actualiza el estado de la entidad cuando se agrega a Home Assistant."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    def _handle_coordinator_update(self) -> None:
        """Actualiza el estado con los datos de carga del SOC."""
        preferences = self.coordinator.data.get(self._account, {}).get("vehicle_charging_prefs", {})
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

        preferences = self.coordinator.data.get(self._account, {}).get("vehicle_charging_prefs", {})

        # Llamada a la API para actualizar las preferencias de carga
        success = await self.coordinator._api.setVehicleChargePreferences(
            account_number=self._account,
            weekday_soc=int(option) if not self._is_weekend else preferences.get("weekdayTargetSoc", None),  # Fijo a 85% para fines de semana
            weekend_soc=int(option) if self._is_weekend else preferences.get("weekendTargetSoc", None),  # Fijo a 85% para días de semana
            weekday_time=preferences.get("weekdayTargetTime", None),  # Hora fija de carga
            weekend_time=preferences.get("weekendTargetTime", None),  # Hora fija de carga
        )

        if success:
            self._current_soc = int(option)
            self.async_write_ha_state()
            
            # 🔄 FORZAR actualización del coordinador para que los sensores reflejen el cambio de inmediato
            await self.coordinator.async_request_refresh()

        else:
            _LOGGER.error(f"❌ No se pudo actualizar el SOC de carga para {self._account}")


class OctopusChargeTime1(CoordinatorEntity, SelectEntity):
    """Selector para elegir la hora de carga por día de la semana."""

    def __init__(self, account: str, coordinator, day: str):
        super().__init__(coordinator)
        self._account = account
        self._day = day.upper()  # Ejemplo: "MONDAY"
        self._attr_name = f"Hora de carga ({day.capitalize()})"
        self._attr_unique_id = f"octopus_charge_time_{account}_{day.lower()}"
        self._attr_options = [f"{h:02d}:00" for h in range(24)]  # Opciones de 00:00 a 23:00
        self._current_time = None

    async def async_added_to_hass(self) -> None:
        """Carga el estado al añadir la entidad."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    def _handle_coordinator_update(self) -> None:
        """Obtiene el horario actual desde la API."""
        schedules = self.coordinator.data.get(self._account, {}).get("device_preferences", {}).get("schedules", [])
        for schedule in schedules:
            if schedule["dayOfWeek"] == self._day:
                self._current_time = schedule["time"]
        self.async_write_ha_state()

    @property
    def current_option(self) -> str | None:
        """Devuelve la hora de carga actual."""
        return self._current_time

    async def async_select_option(self, option: str) -> None:
        """Actualiza la hora de carga y llama a la API."""
        _LOGGER.info(f"🔄 Actualizando hora de carga para {self._day}: {option}")
        await self._update_charge_preferences(time=option)
    
    async def _update_charge_preferences(self, time: str = None, max_soc: str = None) -> None:
        """Llama a la API para actualizar los valores de carga."""

        # Obtener lista de dispositivos
        devices = self.coordinator.data.get(self._account, {}).get("devices", [])

        if not devices:
            _LOGGER.error("❌ No se encontraron dispositivos en los datos del coordinador.")
            return

        # Tomar el primer dispositivo (o modificar la lógica si hay más de uno)
        device_id = devices[0].get("id") if devices else None

        if not device_id:
            _LOGGER.error("❌ No se encontró un ID de dispositivo válido.")
            return
        schedules = []
        for day in ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]:
            schedules.append({
                "dayOfWeek": day,
                "time": time if day == self._day else self.coordinator.data.get(self._account, {}).get("device_preferences", {}).get("schedules", {}).get(day, {}).get("time", "09:00"),
                "max": max_soc if day == self._day else self.coordinator.data.get(self._account, {}).get("device_preferences", {}).get("schedules", {}).get(day, {}).get("max", "90"),
            })

        success = await self.coordinator._api.set_device_preferences(
            device_id= device_id,
            mode= "CHARGE",
            unit= "PERCENTAGE",
            schedules= schedules,
        )

        if success:
            self._current_time = time
            self.async_write_ha_state()
        else:
            _LOGGER.error(f"❌ No se pudo actualizar la hora de carga para {self._day}")


class OctopusChargeSoc1(CoordinatorEntity, SelectEntity):
    """Selector para elegir el SOC máximo por día de la semana."""

    def __init__(self, account: str, coordinator, day: str):
        super().__init__(coordinator)
        self._account = account
        self._day = day.upper()  # Ejemplo: "MONDAY"
        self._attr_name = f"SOC de carga ({day.capitalize()})"
        self._attr_unique_id = f"octopus_charge_soc_{account}_{day.lower()}"
        self._attr_options = [str(i) for i in range(0, 101, 5)]  # 0-100% en pasos de 5
        self._current_soc = None

    async def async_added_to_hass(self) -> None:
        """Carga el estado al añadir la entidad."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    def _handle_coordinator_update(self) -> None:
        """Obtiene el SOC actual desde la API."""
        schedules = self.coordinator.data.get(self._account, {}).get("device_preferences", {}).get("schedules", [])
        for schedule in schedules:
            if schedule["dayOfWeek"] == self._day:
                self._current_soc = schedule["max"]
        self.async_write_ha_state()

    @property
    def current_option(self) -> str | None:
        """Devuelve el SOC máximo actual."""
        return str(self._current_soc) if self._current_soc is not None else None

    async def async_select_option(self, option: str) -> None:
        """Actualiza el SOC máximo y llama a la API."""
        _LOGGER.info(f"🔄 Actualizando SOC de carga para {self._day}: {option}%")
        await self._update_charge_preferences(max_soc=option)
    
    async def _update_charge_preferences(self, time: str = None, max_soc: str = None) -> None:
        """Llama a la API para actualizar los valores de carga."""
        
        # Obtener lista de dispositivos
        devices = self.coordinator.data.get(self._account, {}).get("devices", [])
    
        if not devices:
            _LOGGER.error("❌ No se encontraron dispositivos en los datos del coordinador.")
            return
    
        # Tomar el primer dispositivo (o modificar la lógica si hay más de uno)
        device_id = devices[0].get("id") if devices else None
    
        if not device_id:
            _LOGGER.error("❌ No se encontró un ID de dispositivo válido.")
            return
        
        schedules = []
        for day in ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]:
            schedules.append({
                "dayOfWeek": day,
                "time": time if day == self._day else self.coordinator.data.get(self._account, {}).get("device_preferences", {}).get("schedules", {}).get(day, {}).get("time", "09:00"),
                "max": max_soc if day == self._day else self.coordinator.data.get(self._account, {}).get("device_preferences", {}).get("schedules", {}).get(day, {}).get("max", "90"),
            })

        success = await self.coordinator._api.set_device_preferences(
            device_id= device_id,
            mode= "CHARGE",
            unit= "PERCENTAGE",
            schedules= schedules,
        )

        if success:
            self._current_soc = int(max_soc)
            self.async_write_ha_state()
        else:
            _LOGGER.error(f"❌ No se pudo actualizar el SOC de carga para {self._day}")

