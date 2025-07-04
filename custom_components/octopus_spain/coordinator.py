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
        _LOGGER.info("🔄 Ejecutando `_async_update_data()`")

        if await self._api.login():
            _LOGGER.info("🔑 Login exitoso en OctopusSpain")
            self._data = {}
            accounts = await self._api.accounts()
            _LOGGER.info(f"📂 Cuentas obtenidas: {accounts}")

            for account in accounts:
                account_data = await self._api.account(account)
                _LOGGER.info(f"📋 Datos de la cuenta {account}: {account_data}")
                vehicle_prefs = await self._api.get_vehicle_charging_preferences(account)

                if not hasattr(self._api, "registered_krakenflex_device"):
                    _LOGGER.error(f"❌ `registered_krakenflex_device` no existe en `OctopusSpain`")
                    krakenflex_device = None
                else:
                    krakenflex_device = await self._api.registered_krakenflex_device(account)
                    _LOGGER.info(f"✅ Datos del Krakenflex Device: {krakenflex_device}")
                    devices = await self._api.devices(account)
                self._data[account] = {
                    **account_data,
                    "krakenflex_device": krakenflex_device,
                    "devices" : devices,
                    "vehicle_charging_prefs": vehicle_prefs
                }

            _LOGGER.info(f"📊 Datos obtenidos y almacenados: {self._data}")

        return self._data
    
    async def set_vehicle_charge_preferences(self, account_number: str, weekday_target_time: str, weekend_target_time: str) -> bool:
        """Actualiza las preferencias de carga del vehículo en la API de Octopus."""
        _LOGGER.info(f"🚗 Enviando nueva configuración de carga para {account_number}: {weekday_target_time} / {weekend_target_time}")
    
        try:
            response = await self._api.setVehicleChargePreferences(
                account_number=account_number,
                weekdayTargetSoc=85,  # Puedes hacer que estos valores sean configurables
                weekendTargetSoc=85,
                weekdayTargetTime=weekday_target_time,
                weekendTargetTime=weekend_target_time,
            )
    
            if response:
                _LOGGER.info(f"✅ Preferencias de carga actualizadas correctamente para {account_number}")
                await self.async_request_refresh()  # Recargar datos después del cambio
                return True
            else:
                _LOGGER.error(f"❌ Error al actualizar las preferencias de carga para {account_number}")
                return False
    
        except Exception as e:
            _LOGGER.error(f"❌ Excepción en `set_vehicle_charge_preferences`: {e}")
            return False

    async def boost_charge(self, account_number: str):
        """Función para ser llamada desde el servicio de Home Assistant."""
        _LOGGER.info(f"⚡ Intentando activar la carga inmediata para la cuenta {account_number}")
        success = await self._api.trigger_boost_charge(account_number)
        if success:
            _LOGGER.info(f"✅ Carga inmediata activada para la cuenta {account_number}")
            await self.async_request_refresh() # Forzamos la actualización para ver el cambio de estado
        else:
            _LOGGER.error(f"❌ Fallo al activar la carga inmediata para la cuenta {account_number}")
        return success


class OctopusHourlyCoordinator(DataUpdateCoordinator):
    """Coordinator para actualizar datos cada hora."""

    def __init__(self, hass: HomeAssistant, email: str, password: str):
        super().__init__(hass=hass, logger=_LOGGER, name="Octopus Hourly Data", update_interval=timedelta(hours=1))
        self._api = OctopusSpain(email, password)
        self._data = {}

    async def _async_update_data(self):
        _LOGGER.info("🔄 Ejecutando `_async_update_data()` (cada hora)")

        if await self._api.login():
            _LOGGER.info("🔑 Login exitoso en OctopusSpain (Hourly Coordinator)")
            self._data = {}
            accounts = await self._api.accounts()
            _LOGGER.info(f"📂 Cuentas obtenidas: {accounts}")

            for account in accounts:
                account_data = await self._api.account(account)
                _LOGGER.info(f"📋 Datos de la cuenta {account}: {account_data}")

                self._data[account] = {
                    **account_data
                }

            _LOGGER.info(f"📊 Datos obtenidos y almacenados (Hourly Coordinator): {self._data}")

        return self._data
    
###Esto revisarlo bien que esta mal
# class OctopusWalletCoordinator(DataUpdateCoordinator):
#     """Coordinador para el sensor Octopus Wallet."""

#     def __init__(self, hass: HomeAssistant, email: str, password: str):
#         super().__init__(hass=hass, logger=_LOGGER, name="Octopus Intelligent Go", update_interval=timedelta(minutes=UPDATE_INTERVAL))
#         self._api = OctopusSpain(email, password)
#         self._data = {}

#     async def _async_update_data(self):
#         _LOGGER.info("🔄 Ejecutando `_async_update_data()`")

#         if await self._api.login():
#             _LOGGER.info("🔑 Login exitoso en OctopusSpain")
#             self._data = {}
#             accounts = await self._api.accounts()
#             _LOGGER.info(f"📂 Cuentas obtenidas: {accounts}")

#             for account in accounts:
#                 account_data = await self._api.account(account)
#                 if account_data:
#                     wallet_balance = account_data.get(self._key, None)  # Aquí obtienes el balance de la wallet o el valor que necesites
#                     if wallet_balance is not None:
#                         self._data[self._account] = wallet_balance
#                     else:
#                         _LOGGER.error(f"❌ ERROR: No wallet balance found for {self._account}")
#                 else:
#                     _LOGGER.error(f"❌ ERROR: No data found for account {self._account}")
#         return self._data

  
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