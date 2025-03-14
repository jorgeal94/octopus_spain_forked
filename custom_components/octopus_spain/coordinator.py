"""Coordinator for Octopus Spain integration."""

import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .octopus_spain import OctopusSpain
from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=5)  # Se actualizará cada 5 minutos

class OctopusIntelligentCoordinator(DataUpdateCoordinator):
    """Gestor de datos centralizado para la integración de Octopus Spain."""

    def __init__(self, hass: HomeAssistant, email: str, password: str):
        """Inicializa el coordinador con las credenciales de acceso."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_coordinator",
            update_interval=UPDATE_INTERVAL,
        )
        self.api = OctopusSpain(email, password)
        self.account_number = None

    async def _async_update_data(self):
        """Obtiene los datos más recientes desde la API de Octopus Spain."""
        _LOGGER.debug("Actualizando datos desde Octopus Spain API...")

        try:
            # Autenticación
            if not await self.api.login():
                raise UpdateFailed("Error al autenticar en Octopus Spain")

            # Obtener cuenta
            accounts = await self.api.accounts()
            if not accounts:
                raise UpdateFailed("No se encontraron cuentas asociadas a este usuario")

            self.account_number = accounts[0]  # Asumimos la primera cuenta si hay varias
            account_data = await self.api.account(self.account_number)

            # Obtener dispositivos
            devices = await self.api.devices(self.account_number)

            return {
                "account": account_data,
                "devices": devices if devices else [],
            }

        except Exception as err:
            _LOGGER.error(f"Error actualizando datos de Octopus Spain: {err}")
            raise UpdateFailed(f"Error obteniendo datos: {err}")
