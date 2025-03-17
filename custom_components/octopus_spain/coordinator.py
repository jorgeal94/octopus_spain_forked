# """Coordinator for Octopus Spain integration."""

import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .octopus_spain import OctopusSpain
from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class OctopusIntelligentCoordinator(DataUpdateCoordinator):

    def __init__(self, hass: HomeAssistant, email: str, password: str):
        super().__init__(hass=hass, logger=_LOGGER, name="Octopus Intelligent Go", update_interval=timedelta(minutes=UPDATE_INTERVAL))
        self._api = OctopusSpain(email, password)
        self._data = {}

    async def _async_update_data(self):
        if await self._api.login():
            self._data = {}
            accounts = await self._api.accounts()
            for account in accounts:
                account_data = await self._api.account(account)
                # 🔍 Verificar si el objeto tiene el método
                if not hasattr(self._api, "registered_krakenflex_device"):
                    _LOGGER.error(f"❌ ERROR: `registered_krakenflex_device` NO existe en `OctopusSpain`")
                else:
                    _LOGGER.info(f"✅ `registered_krakenflex_device` existe en `OctopusSpain`")

                krakenflex_device = await self._api.registered_krakenflex_device(account)

        return self._data
    
# class OctopusIntelligentCoordinator(DataUpdateCoordinator):
#     """Gestor de datos centralizado para la integración de Octopus Spain."""

#     def __init__(self, hass: HomeAssistant, email: str, password: str):
#         """Inicializa el coordinador con las credenciales de acceso."""
#         super().__init__(
#             hass,
#             _LOGGER,
#             name=f"{DOMAIN}_coordinator",
#             update_interval=UPDATE_INTERVAL,
#         )
#         self.api = OctopusSpain(email, password)
#         self.account_number = None

#     async def _async_update_data(self):
#         """Obtiene los datos más recientes desde la API de Octopus Spain."""
#         _LOGGER.debug("Actualizando datos desde Octopus Spain API...")

#         try:
#             # Autenticación
#             if not await self.api.login():
#                 raise UpdateFailed("Error al autenticar en Octopus Spain")

#             # Obtener cuenta
#             accounts = await self.api.accounts()
#             if not accounts:
#                 raise UpdateFailed("No se encontraron cuentas asociadas a este usuario")

#             self.account_number = accounts[0]  # Asumimos la primera cuenta si hay varias
#             account_data = await self.api.account(self.account_number)

#             # Obtener dispositivos
#             devices = await self.api.devices(self.account_number)

#             return {
#                 "account": account_data,
#                 "devices": devices if devices else [],
#             }

#         except Exception as err:
#             _LOGGER.error(f"Error actualizando datos de Octopus Spain: {err}")
#             raise UpdateFailed(f"Error obteniendo datos: {err}")

# from datetime import timedelta
# from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
# from .octopus_spain import OctopusSpain
# from homeassistant.core import HomeAssistant
# _LOGGER = logging.getLogger(__name__)

# class OctopusIntelligentGo(DataUpdateCoordinator):
#     """Coordinador específico para la gestión de carga del vehículo."""
    
#     def __init__(self, hass: HomeAssistant, email: str, password: str):
#         super().__init__(hass=hass, logger=_LOGGER, name="Octopus Intelligent Go", update_interval=timedelta(minutes=1))
#         self._api = OctopusSpain(email, password)
#         self._data = {}

#     async def _async_update_data(self):
#         if await self._api.login():
#             self._data = {}
#             accounts = await self._api.accounts()
#             for account in accounts:
#                 krakenflex_device = await self._api.devices(account)
#                 self._data[account] = {
#                     "krakenflex_device": krakenflex_device,
#                 }
#         return self._data

    # async def set_device_preferences(self, account_id: str, day_of_week: str, soc: int, time: str):
    #     """Actualiza las preferencias del dispositivo."""
    #     if await self._api.login():
    #         device_id = self._data[account_id]["krakenflex_device"]["id"]
    #         schedules = [{"dayOfWeek": day_of_week.upper(), "max": soc, "time": time}]
            
    #         success = await self._api.set_device_preferences(
    #             account_id=account_id,
    #             device_id=device_id,
    #             mode="CHARGE",
    #             schedules=schedules,
    #             unit="PERCENTAGE"
    #         )

    #         if success:
    #             self._data[account_id]["vehicle_charging_prefs"][day_of_week] = {
    #                 "max": soc,
    #                 "time": time
    #             }
    #             self.async_update_listeners()
    #             return True
    #     return False