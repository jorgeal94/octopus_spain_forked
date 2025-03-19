from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
import logging

from .octopus_spain import OctopusSpain

_LOGGER = logging.getLogger(__name__)

from .const import (
    CONF_PASSWORD,
    CONF_EMAIL, UPDATE_INTERVAL
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Configurar selectores de Octopus Spain."""
    _LOGGER.info("🛠️ Configurando selectores de Octopus Spain")

    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    api = OctopusSpain(email, password)

    accounts = await api.accounts()

    selects = [VehicleChargePreferencesSelect(account, api) for account in accounts]

    if selects:
        async_add_entities(selects)
        _LOGGER.info(f"✅ Se han añadido {len(selects)} selectores")
    else:
        _LOGGER.warning("⚠️ No se ha añadido ningún selector")


class VehicleChargePreferencesSelect(SelectEntity):
    """Entidad para modificar las preferencias de carga del vehículo."""

    def __init__(self, account: str, api: OctopusSpain):
        """Inicializar la entidad de selección."""
        self._account = account
        self._api = api
        self._attr_name = f"Preferencias de carga ({account})"
        self._attr_unique_id = f"octopus_charge_prefs_{account}"
        self._attr_options = ["85% a las 09:00", "80% a las 08:00", "90% a las 10:00"]
        self._attr_current_option = "85% a las 09:00"

    async def async_select_option(self, option: str):
        """Actualizar las preferencias de carga."""
        mapping = {
            "85% a las 09:00": (85, 85, "09:00", "09:00"),
            "80% a las 08:00": (80, 80, "08:00", "08:00"),
            "90% a las 10:00": (90, 90, "10:00", "10:00"),
        }
        weekday_soc, weekend_soc, weekday_time, weekend_time = mapping[option]

        result = await self._api.set_vehicle_charge_preferences(
            self._account, weekday_soc, weekend_soc, weekday_time, weekend_time
        )

        if result:
            _LOGGER.info(f"✅ Preferencias de carga actualizadas correctamente en la API: {result}")
            self._attr_current_option = option
            self.async_write_ha_state()
        else:
            _LOGGER.error(f"❌ Error al actualizar preferencias: {result}")        