# import logging
# from datetime import timedelta
# from typing import Mapping, Any

# from homeassistant.helpers.typing import StateType
# from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
# from .const import (
#     CONF_PASSWORD,
#     CONF_EMAIL, UPDATE_INTERVAL
# )

# from homeassistant.const import (
#     CURRENCY_EURO,
# )

# from homeassistant.components.sensor import (
#     SensorEntityDescription, SensorEntity, SensorStateClass
# )
# from homeassistant.config_entries import ConfigEntry
# from homeassistant.core import HomeAssistant, callback
# from homeassistant.helpers.entity_platform import AddEntitiesCallback
# from .lib.octopus_spain import OctopusSpain

# _LOGGER = logging.getLogger(__name__)


# async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
#     email = entry.data[CONF_EMAIL]
#     password = entry.data[CONF_PASSWORD]

#     sensors = []
#     coordinator = OctopusCoordinator(hass, email, password)
#     await coordinator.async_config_entry_first_refresh()
#     intelligentcoordinator = OctopusIntelligentCoordinator(hass, email, password)
#     await intelligentcoordinator.async_config_entry_first_refresh()

#     accounts = coordinator.data.keys()
#     for account in accounts:
#         sensors.append(OctopusWallet(account, 'solar_wallet', 'Solar Wallet', coordinator, len(accounts) == 1))
#         sensors.append(OctopusWallet(account, 'octopus_credit', 'Octopus Credit', coordinator, len(accounts) == 1))
#         sensors.append(OctopusInvoice(account, coordinator, len(accounts) == 1))
#         sensors.append(OctopusKrakenflexDevice(account, intelligentcoordinator, len(accounts) == 1))  # Nuevo sensor
#         sensors.append(OctopusVehicleChargingPreferencesSensor(account, intelligentcoordinator, single=False))

#     async_add_entities(sensors)


# # class OctopusCoordinator(DataUpdateCoordinator):

# #     def __init__(self, hass: HomeAssistant, email: str, password: str):
# #         super().__init__(hass=hass, logger=_LOGGER, name="Octopus Spain", update_interval=timedelta(hours=UPDATE_INTERVAL))
# #         self._api = OctopusSpain(email, password)
# #         self._data = {}

# #     async def _async_update_data(self):
# #         if await self._api.login():
# #             self._data = {}
# #             accounts = await self._api.accounts()
# #             for account in accounts:
# #                 self._data[account] = await self._api.account(account)

# #         return self._data


# class OctopusWallet(CoordinatorEntity, SensorEntity):

#     def __init__(self, account: str, key: str, name: str, coordinator, single: bool):
#         super().__init__(coordinator=coordinator)
#         self._state = None
#         self._key = key
#         self._account = account
#         self._attrs: Mapping[str, Any] = {}
#         self._attr_name = f"{name}" if single else f"{name} ({account})"
#         self._attr_unique_id = f"{key}_{account}"
#         self.entity_description = SensorEntityDescription(
#             key=f"{key}_{account}",
#             icon="mdi:piggy-bank-outline",
#             native_unit_of_measurement=CURRENCY_EURO,
#             state_class=SensorStateClass.MEASUREMENT
#         )

#     async def async_added_to_hass(self) -> None:
#         await super().async_added_to_hass()
#         self._handle_coordinator_update()

#     @callback
#     def _handle_coordinator_update(self) -> None:
#         """Handle updated data from the coordinator."""
#         self._state = self.coordinator.data[self._account][self._key]
#         self.async_write_ha_state()

#     @property
#     def native_value(self) -> StateType:
#         return self._state


# class OctopusInvoice(CoordinatorEntity, SensorEntity):

#     def __init__(self, account: str, coordinator, single: bool):
#         super().__init__(coordinator=coordinator)
#         self._state = None
#         self._account = account
#         self._attrs: Mapping[str, Any] = {}
#         self._attr_name = "Última Factura Octopus" if single else f"Última Factura Octopus ({account})"
#         self._attr_unique_id = f"last_invoice_{account}"
#         self.entity_description = SensorEntityDescription(
#             key=f"last_invoice_{account}",
#             icon="mdi:currency-eur",
#             native_unit_of_measurement=CURRENCY_EURO,
#             state_class=SensorStateClass.MEASUREMENT
#         )

#     async def async_added_to_hass(self) -> None:
#         await super().async_added_to_hass()
#         self._handle_coordinator_update()

#     @callback
#     def _handle_coordinator_update(self) -> None:
#         """Handle updated data from the coordinator."""
#         data = self.coordinator.data[self._account]['last_invoice']
#         self._state = data['amount']
#         self._attrs = {
#             'Inicio': data['start'],
#             'Fin': data['end'],
#             'Emitida': data['issued']
#         }
#         self.async_write_ha_state()

#     @property
#     def native_value(self) -> StateType:
#         return self._state

#     @property
#     def extra_state_attributes(self) -> Mapping[str, Any] | None:
#         return self._attrs

# class OctopusCoordinator(DataUpdateCoordinator):

#     def __init__(self, hass: HomeAssistant, email: str, password: str):
#         super().__init__(hass=hass, logger=_LOGGER, name="Octopus Spain", update_interval=timedelta(hours=UPDATE_INTERVAL))
#         self._api = OctopusSpain(email, password)
#         self._data = {}

#     async def _async_update_data(self):
#         if await self._api.login():
#             self._data = {}
#             accounts = await self._api.accounts()
#             for account in accounts:
#                 account_data = await self._api.account(account)
#                 krakenflex_device = await self._api.registered_krakenflex_device(account)
#                 vehicle_prefs = await self._api.get_vehicle_charging_preferences(account)
#                 self._data[account] = {
#                     **account_data,
#                     # "krakenflex_device": krakenflex_device,
#                     # "vehicle_charging_prefs": vehicle_prefs
#                 }

#         return self._data

# ####################################

# class OctopusIntelligentCoordinator(DataUpdateCoordinator):

#     def __init__(self, hass: HomeAssistant, email: str, password: str):
#         super().__init__(hass=hass, logger=_LOGGER, name="Octopus Intelligent Go", update_interval=timedelta(minutes=UPDATE_INTERVAL))
#         self._api = OctopusSpain(email, password)
#         self._data = {}

#     async def _async_update_data(self):
#         if await self._api.login():
#             self._data = {}
#             accounts = await self._api.accounts()
#             for account in accounts:
#                 account_data = await self._api.account(account)
#                 krakenflex_device = await self._api.registered_krakenflex_device(account)
#                 vehicle_prefs = await self._api.get_vehicle_charging_preferences(account)
#                 self._data[account] = {
#                     **account_data,
#                     "krakenflex_device": krakenflex_device,
#                     "vehicle_charging_prefs": vehicle_prefs
#                 }

#         return self._data

# class OctopusKrakenflexDevice(CoordinatorEntity, SensorEntity):

#     def __init__(self, account: str, coordinator, single: bool):
#         super().__init__(coordinator=coordinator)
#         self._account = account
#         self._state = None
#         self._attrs: Mapping[str, Any] = {}
#         self._attr_name = "Krakenflex Device" if single else f"Krakenflex Device ({account})"
#         self._attr_unique_id = f"krakenflex_device_{account}"
#         self.entity_description = SensorEntityDescription(
#             key=f"krakenflex_device_{account}",
#             icon="mdi:car-electric",
#         )  # Eliminamos `state_class=SensorStateClass.MEASUREMENT`

#     async def async_added_to_hass(self) -> None:
#         await super().async_added_to_hass()
#         self._handle_coordinator_update()

#     @callback
#     def _handle_coordinator_update(self) -> None:
#         """Actualiza el estado con los datos del dispositivo Krakenflex."""
#         device = self.coordinator.data[self._account].get("krakenflex_device", {})
#         if device:
#             self._state = device.get("status")  # Aquí puede ser un string como "Live"
#             self._attrs = {
#                 "krakenflexDeviceId": device.get("krakenflexDeviceId"),
#                 "provider": device.get("provider"),
#                 "vehicleMake": device.get("vehicleMake"),
#                 "vehicleModel": device.get("vehicleModel"),
#                 "vehicleBatterySizeInKwh": device.get("vehicleBatterySizeInKwh"),
#                 "chargePointMake": device.get("chargePointMake"),
#                 "chargePointModel": device.get("chargePointModel"),
#                 "chargePointPowerInKw": device.get("chargePointPowerInKw"),
#                 "suspended": device.get("suspended"),
#                 "hasToken": device.get("hasToken"),
#                 "createdAt": device.get("createdAt"),
#             }
#         self.async_write_ha_state()

#     @property
#     def native_value(self) -> str | None:
#         """Devuelve el estado del dispositivo Krakenflex (como 'Live', 'Charging', etc.)."""
#         return self._state  # Es un string, por lo que no se puede forzar a float

#     @property
#     def extra_state_attributes(self) -> Mapping[str, Any] | None:
#         """Devuelve atributos adicionales del dispositivo Krakenflex."""
#         return self._attrs

# class OctopusVehicleChargingPreferencesSensor(CoordinatorEntity, SensorEntity):

#     def __init__(self, account: str, coordinator, single: bool):
#         super().__init__(coordinator=coordinator)
#         self._account = account
#         self._state = None
#         self._attrs: Mapping[str, Any] = {}
#         self._attr_name = "Vehicle Charging Preferences" if single else f"Vehicle Charging ({account})"
#         self._attr_unique_id = f"vehicle_charging_prefs_{account}"
#         self.entity_description = SensorEntityDescription(
#             key=f"vehicle_charging_prefs_{account}",
#             icon="mdi:ev-station",
#         )

#     async def async_added_to_hass(self) -> None:
#         await super().async_added_to_hass()
#         self._handle_coordinator_update()

#     @callback
#     def _handle_coordinator_update(self) -> None:
#         """Actualiza el estado con los datos de preferencias de carga del vehículo."""
#         prefs = self.coordinator.data[self._account].get("vehicle_charging_prefs", {})

#         if prefs:
#             self._state = prefs.get("weekdayTargetSoc")  # Valor por defecto: SOC entre semana
#             self._attrs = {
#                 "weekday_target_time": prefs.get("weekdayTargetTime"),
#                 "weekday_target_soc": prefs.get("weekdayTargetSoc"),
#                 "weekend_target_time": prefs.get("weekendTargetTime"),
#                 "weekend_target_soc": prefs.get("weekendTargetSoc"),
#             }

#         self.async_write_ha_state()

#     @property
#     def native_value(self) -> int | None:
#         """Devuelve el SOC objetivo entre semana."""
#         return self._state

#     @property
#     def extra_state_attributes(self) -> Mapping[str, Any] | None:
#         """Devuelve atributos adicionales con más datos de carga."""
#         return self._attrs


########################################OJOAKI
"""Sensor for Octopus Spain integration."""

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Configura los sensores de la integración."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    """Configura los sensores de la integración."""
    _LOGGER.info(f"Datos de la entrada: {entry.data}")

    # Intenta obtener el número de cuenta de la entrada de configuración
    account_number = entry.data.get("account_number")
    if not account_number:
        _LOGGER.error("No se encontró account_number en los datos de la entrada")
        return
    else:
        _LOGGER.info(f"account_number encontrado: {account_number}")
    
    try:
        devices = await coordinator.async_get_devices(account_number)
    except Exception as e:
        _LOGGER.error(f"Error al obtener dispositivos: {e}")
        return

    _LOGGER.info(f"Dispositivos: {devices}")
    
    if not devices:
        _LOGGER.warning("No se encontraron dispositivos")
        return

    sensors = []

    for device in devices:
        _LOGGER.info(f"Dispositivo: {device}")
        sensors.append(OctopusVehicleStateSensor(coordinator, device))
        sensors.append(OctopusChargeLimitSensor(coordinator, device))

    _LOGGER.info(f"Sensores creados: {len(sensors)}")
    async_add_entities(sensors, update_before_add=True)


class OctopusVehicleStateSensor(CoordinatorEntity, SensorEntity):
    """Sensor que muestra el estado del vehículo eléctrico."""

    def __init__(self, coordinator, device):
        """Inicializa el sensor."""
        super().__init__(coordinator)
        self._device_id = device.get("id")
        self._attr_name = f"{device.get('name', 'Vehículo')} Estado"
        self._attr_unique_id = f"{self._device_id}_state"

    @property
    def state(self):
        """Devuelve el estado actual del vehículo."""
        device_data = self._get_device_data()
        return device_data.get("status", {}).get("currentState", "UNKNOWN")

    @property
    def extra_state_attributes(self):
        """Atributos adicionales del sensor."""
        device_data = self._get_device_data()
        status = device_data.get("status", {})

        return {
            "Estado actual": status.get("current", "UNKNOWN"),
            "Suspendido": status.get("isSuspended", False),
            "Límite de carga violado": status.get("stateOfChargeLimit", {}).get("isLimitViolated", False),
            "Última actualización": status.get("stateOfChargeLimit", {}).get("timestamp", "UNKNOWN"),
        }

    def _get_device_data(self):
        """Obtiene los datos actualizados del dispositivo desde el Coordinator."""
        return next(
            (d for d in self.coordinator.data.get("data", {}).get("devices", []) if d.get("id") == self._device_id),
            {}
        )


class OctopusChargeLimitSensor(CoordinatorEntity, SensorEntity):
    """Sensor que muestra el límite de carga del vehículo."""

    def __init__(self, coordinator, device):
        """Inicializa el sensor."""
        super().__init__(coordinator)
        self._device_id = device.get("id")
        self._attr_name = f"{device.get('name', 'Vehículo')} Límite de Carga"
        self._attr_unique_id = f"{self._device_id}_charge_limit"

    @property
    def state(self):
        """Devuelve el límite de carga en porcentaje."""
        device_data = self._get_device_data()
        return device_data.get("status", {}).get("stateOfChargeLimit", {}).get("upperSocLimit", "UNKNOWN")

    @property
    def unit_of_measurement(self):
        """Unidad de medida."""
        return "%"

    @property
    def extra_state_attributes(self):
        """Atributos adicionales del sensor."""
        device_data = self._get_device_data()

        return {
            "Modelo": device_data.get("model", "UNKNOWN"),
            "Fabricante": device_data.get("make", "UNKNOWN"),
            "Modo de carga": device_data.get("preferences", {}).get("mode", "UNKNOWN"),
            "Horario de carga": device_data.get("preferences", {}).get("schedules", []),
        }

    def _get_device_data(self):
        """Obtiene los datos actualizados del dispositivo desde el Coordinator."""
        return next(
            (d for d in self.coordinator.data.get("data", {}).get("devices", []) if d.get("id") == self._device_id),
            {}
        )
