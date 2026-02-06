import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OctopusIntelligentCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Configura los botones de la integración Octopus Spain."""
    _LOGGER.info("🛠️ Configurando botones de Octopus Spain")

    intelligentcoordinator = hass.data[DOMAIN].get("intelligent_coordinator")
    if not intelligentcoordinator:
        _LOGGER.error("❌ intelligent_coordinator no está disponible en hass.data para la plataforma de botones.")
        return

    buttons = []
    accounts = intelligentcoordinator.data.keys()
    for account in accounts:
        # Añadimos un botón de carga inmediata por cada cuenta que tenga dispositivos
        if intelligentcoordinator.data[account].get("devices"):
            _LOGGER.info(f"📡 Creando botón de carga inmediata para la cuenta {account}")
            devices = intelligentcoordinator.data[account].get("devices", [])
            if devices:
                device = devices[0]
                device_id = device.get("id")  # ID del dispositivo de la API
                device_name = device.get("name", f"Dispositivo {account}")
                _LOGGER.info(f"✅ Botón con device_id={device_id}, device_name={device_name}")
                buttons.append(OctopusBoostChargeButton(account, intelligentcoordinator, device_id, device_name))

    if buttons:
        async_add_entities(buttons)
        _LOGGER.info(f"✅ Se han añadido {len(buttons)} botones")
    else:
        _LOGGER.warning("⚠️ No se ha añadido ningún botón de carga inmediata")

class OctopusBoostChargeButton(CoordinatorEntity, ButtonEntity):
    """Define el botón para activar la carga inmediata (boost)."""

    def __init__(self, account: str, coordinator: OctopusIntelligentCoordinator, device_id: str = "", device_name: str = ""):
        """Inicializa el botón."""
        super().__init__(coordinator)
        self._account = account
        self._device_id = device_id
        self._device_name = device_name
        
        # Nombre que se mostrará en Home Assistant
        self._attr_name = f"Carga Inmediata ({account})"
        
        # ID único para la entidad
        self._attr_unique_id = f"octopus_boost_charge_{account}"
        
        # Icono para el botón
        self._attr_icon = "mdi:rocket-launch"
        
        # Vincular al dispositivo
        self._attr_device_info = {"identifiers": {(DOMAIN, device_id)}} if device_id else None

    async def async_press(self) -> None:
        """Gestiona el evento de pulsar el botón."""
        _LOGGER.info(f"🔘 Botón de carga inmediata presionado para la cuenta {self._account}")
        # Llama a la función que ya habíamos creado en el coordinador
        await self.coordinator.boost_charge(self._account)