# """Balance Neto"""
# from __future__ import annotations

# from homeassistant.config_entries import ConfigEntry
# from homeassistant.const import Platform
# from homeassistant.core import HomeAssistant

# from .const import DOMAIN

# PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SELECT]


# async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
#     """Set up the integration from a config entry."""
#     await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

#     entry.async_on_unload(entry.add_update_listener(_async_update_options))
#     return True


# async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
#     """Unload a config entry."""
#     return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


# async def _async_update_options(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
#     """Handle options update."""
#     hass.config_entries.async_update_entry(
#         config_entry, data={**config_entry.data, **config_entry.options}
#     )
#     await hass.config_entries.async_reload(config_entry.entry_id)

"""Octopus Spain integration for Home Assistant."""

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import Platform
from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD
from .coordinator import OctopusIntelligentCoordinator

_LOGGER = logging.getLogger(__name__)


PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SELECT]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Octopus Spain component."""
    _LOGGER.info("Octopus Spain integration setup")
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Octopus Spain from a config entry."""
    _LOGGER.info("Setting up Octopus Spain entry")

    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]

    coordinator = OctopusIntelligentCoordinator(hass, email, password)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Configurar plataformas de integración
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an Octopus Spain entry."""
    _LOGGER.info("Unloading Octopus Spain entry")
    
    if entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)

    return await hass.config_entries.async_forward_entry_unload(entry, "sensor")
