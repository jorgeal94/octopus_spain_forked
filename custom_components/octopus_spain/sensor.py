import logging
from datetime import timedelta
from typing import Mapping, Any

from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from .const import (
    CONF_PASSWORD,
    CONF_EMAIL, UPDATE_INTERVAL
)

from homeassistant.const import (
    CURRENCY_EURO,
)

from homeassistant.components.sensor import (
    SensorEntityDescription, SensorEntity, SensorStateClass
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .lib.octopus_spain import OctopusSpain

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]

    sensors = []
    coordinator = OctopusCoordinator(hass, email, password)
    await coordinator.async_config_entry_first_refresh()
    intelligentcoordinator = OctopusIntelligentCoordinator(hass, email, password)
    await intelligentcoordinator.async_config_entry_first_refresh()

    accounts = coordinator.data.keys()
    for account in accounts:
        sensors.append(OctopusWallet(account, 'solar_wallet', 'Solar Wallet', coordinator, len(accounts) == 1))
        sensors.append(OctopusWallet(account, 'octopus_credit', 'Octopus Credit', coordinator, len(accounts) == 1))
        sensors.append(OctopusInvoice(account, coordinator, len(accounts) == 1))
        sensors.append(OctopusKrakenflexDevice(account, intelligentcoordinator, len(accounts) == 1))  # Nuevo sensor
        sensors.append(OctopusVehicleChargingPreferencesSensor(account, intelligentcoordinator, single=False))

    async_add_entities(sensors)


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
#                 self._data[account] = await self._api.account(account)

#         return self._data


class OctopusWallet(CoordinatorEntity, SensorEntity):

    def __init__(self, account: str, key: str, name: str, coordinator, single: bool):
        super().__init__(coordinator=coordinator)
        self._state = None
        self._key = key
        self._account = account
        self._attrs: Mapping[str, Any] = {}
        self._attr_name = f"{name}" if single else f"{name} ({account})"
        self._attr_unique_id = f"{key}_{account}"
        self.entity_description = SensorEntityDescription(
            key=f"{key}_{account}",
            icon="mdi:piggy-bank-outline",
            native_unit_of_measurement=CURRENCY_EURO,
            state_class=SensorStateClass.MEASUREMENT
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._state = self.coordinator.data[self._account][self._key]
        self.async_write_ha_state()

    @property
    def native_value(self) -> StateType:
        return self._state


class OctopusInvoice(CoordinatorEntity, SensorEntity):

    def __init__(self, account: str, coordinator, single: bool):
        super().__init__(coordinator=coordinator)
        self._state = None
        self._account = account
        self._attrs: Mapping[str, Any] = {}
        self._attr_name = "Última Factura Octopus" if single else f"Última Factura Octopus ({account})"
        self._attr_unique_id = f"last_invoice_{account}"
        self.entity_description = SensorEntityDescription(
            key=f"last_invoice_{account}",
            icon="mdi:currency-eur",
            native_unit_of_measurement=CURRENCY_EURO,
            state_class=SensorStateClass.MEASUREMENT
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        data = self.coordinator.data[self._account]['last_invoice']
        self._state = data['amount']
        self._attrs = {
            'Inicio': data['start'],
            'Fin': data['end'],
            'Emitida': data['issued']
        }
        self.async_write_ha_state()

    @property
    def native_value(self) -> StateType:
        return self._state

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        return self._attrs

class OctopusCoordinator(DataUpdateCoordinator):

    def __init__(self, hass: HomeAssistant, email: str, password: str):
        super().__init__(hass=hass, logger=_LOGGER, name="Octopus Spain", update_interval=timedelta(hours=UPDATE_INTERVAL))
        self._api = OctopusSpain(email, password)
        self._data = {}

    async def _async_update_data(self):
        if await self._api.login():
            self._data = {}
            accounts = await self._api.accounts()
            for account in accounts:
                account_data = await self._api.account(account)
                krakenflex_device = await self._api.registered_krakenflex_device(account)
                vehicle_prefs = await self._api.get_vehicle_charging_preferences(account)
                self._data[account] = {
                    **account_data,
                    # "krakenflex_device": krakenflex_device,
                    # "vehicle_charging_prefs": vehicle_prefs
                }

        return self._data

####################################

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
                krakenflex_device = await self._api.registered_krakenflex_device(account)
                vehicle_prefs = await self._api.get_vehicle_charging_preferences(account)
                self._data[account] = {
                    **account_data,
                    "krakenflex_device": krakenflex_device,
                    "vehicle_charging_prefs": vehicle_prefs
                }

        return self._data

class OctopusKrakenflexDevice(CoordinatorEntity, SensorEntity):

    def __init__(self, account: str, coordinator, single: bool):
        super().__init__(coordinator=coordinator)
        self._account = account
        self._state = None
        self._attrs: Mapping[str, Any] = {}
        self._attr_name = "Krakenflex Device" if single else f"Krakenflex Device ({account})"
        self._attr_unique_id = f"krakenflex_device_{account}"
        self.entity_description = SensorEntityDescription(
            key=f"krakenflex_device_{account}",
            icon="mdi:car-electric",
        )  # Eliminamos `state_class=SensorStateClass.MEASUREMENT`

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Actualiza el estado con los datos del dispositivo Krakenflex."""
        device = self.coordinator.data[self._account].get("krakenflex_device", {})
        if device:
            self._state = device.get("status")  # Aquí puede ser un string como "Live"
            self._attrs = {
                "krakenflexDeviceId": device.get("krakenflexDeviceId"),
                "provider": device.get("provider"),
                "vehicleMake": device.get("vehicleMake"),
                "vehicleModel": device.get("vehicleModel"),
                "vehicleBatterySizeInKwh": device.get("vehicleBatterySizeInKwh"),
                "chargePointMake": device.get("chargePointMake"),
                "chargePointModel": device.get("chargePointModel"),
                "chargePointPowerInKw": device.get("chargePointPowerInKw"),
                "suspended": device.get("suspended"),
                "hasToken": device.get("hasToken"),
                "createdAt": device.get("createdAt"),
            }
        self.async_write_ha_state()

    @property
    def native_value(self) -> str | None:
        """Devuelve el estado del dispositivo Krakenflex (como 'Live', 'Charging', etc.)."""
        return self._state  # Es un string, por lo que no se puede forzar a float

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Devuelve atributos adicionales del dispositivo Krakenflex."""
        return self._attrs

class OctopusVehicleChargingPreferencesSensor(CoordinatorEntity, SensorEntity):

    def __init__(self, account: str, coordinator, single: bool):
        super().__init__(coordinator=coordinator)
        self._account = account
        self._state = None
        self._attrs: Mapping[str, Any] = {}
        self._attr_name = "Vehicle Charging Preferences" if single else f"Vehicle Charging ({account})"
        self._attr_unique_id = f"vehicle_charging_prefs_{account}"
        self.entity_description = SensorEntityDescription(
            key=f"vehicle_charging_prefs_{account}",
            icon="mdi:ev-station",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Actualiza el estado con los datos de preferencias de carga del vehículo."""
        prefs = self.coordinator.data[self._account].get("vehicle_charging_prefs", {})

        if prefs:
            self._state = prefs.get("weekdayTargetSoc")  # Valor por defecto: SOC entre semana
            self._attrs = {
                "weekday_target_time": prefs.get("weekdayTargetTime"),
                "weekday_target_soc": prefs.get("weekdayTargetSoc"),
                "weekend_target_time": prefs.get("weekendTargetTime"),
                "weekend_target_soc": prefs.get("weekendTargetSoc"),
            }

        self.async_write_ha_state()

    @property
    def native_value(self) -> int | None:
        """Devuelve el SOC objetivo entre semana."""
        return self._state

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Devuelve atributos adicionales con más datos de carga."""
        return self._attrs