import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD
from .octopus_spain import OctopusSpain

_LOGGER = logging.getLogger(__name__)

class OctopusSpainConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Maneja el flujo de configuración de la integración Octopus Spain."""

    async def async_step_user(self, user_input=None):
        """Controla el paso inicial del flujo de configuración."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=self._get_data_schema())

        email = user_input[CONF_EMAIL]
        password = user_input[CONF_PASSWORD]

        # Aquí validamos las credenciales mediante la API de OctopusSpain
        octopus_spain = OctopusSpain(email, password)
        if not await octopus_spain.login():
            return self.async_show_form(
                step_id="user",
                errors={"base": "invalid_credentials"},
                data_schema=self._get_data_schema(),
            )

        # Si las credenciales son correctas, guardamos la configuración
        return self.async_create_entry(
            title=f"Octopus Spain {email}",
            data=user_input
        )

    def _get_data_schema(self):
        """Devuelve el esquema de datos para el formulario de configuración."""
        return vol.Schema({
            vol.Required(CONF_EMAIL): str,
            vol.Required(CONF_PASSWORD): str,
        })



# from __future__ import annotations

# import logging
# from typing import Any

# import voluptuous as vol

# from homeassistant.core import callback

# from homeassistant import config_entries
# from homeassistant.data_entry_flow import FlowResult
# from homeassistant.helpers.selector import (
#     TextSelector,
#     TextSelectorType,
#     TextSelectorConfig
# )

# from .const import *
# from .octopus_spain import OctopusSpain

# _LOGGER = logging.getLogger(__name__)

# SCHEMA = vol.Schema(
#     {
#         vol.Required(CONF_EMAIL): TextSelector(
#             TextSelectorConfig(multiline=False, type=TextSelectorType.EMAIL)
#         ),
#         vol.Required(CONF_PASSWORD): TextSelector(
#             TextSelectorConfig(multiline=False, type=TextSelectorType.PASSWORD)
#         ),
#     }
# )


# class PlaceholderHub:
#     def __init__(self, email: str, password: str) -> None:
#         """Initialize."""
#         self.email = email
#         self.password = password


# class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
#     VERSION = 1

#     @staticmethod
#     @callback
#     def async_get_options_flow(config_entry):
#         return OptionFlowHandler(config_entry)

#     async def async_step_user(
#             self, user_input: dict[str, Any] | None = None
#     ) -> FlowResult:
#         if user_input is None:
#             return self.async_show_form(step_id="user", data_schema=SCHEMA)

#         api = OctopusSpain(user_input[CONF_EMAIL], user_input[CONF_PASSWORD])
#         if await api.login():
#             return self.async_create_entry(data=user_input, title="Octopus Spain")
#         else:
#             return self.async_show_form(step_id="user", data_schema=SCHEMA, errors={'base': 'invalid_auth'})


# class OptionFlowHandler(config_entries.OptionsFlow):
#     def __init__(self, config_entry):
#         self.config_entry = config_entry

#     async def async_step_init(self, user_input=None):
#         email = self.config_entry.options.get(
#             CONF_EMAIL, self.config_entry.data[CONF_EMAIL]
#         )
#         password = self.config_entry.options.get(
#             CONF_PASSWORD, self.config_entry.data[CONF_PASSWORD]
#         )

#         schema = vol.Schema(
#             {
#                 vol.Required(CONF_EMAIL, default=email): TextSelector(
#                     TextSelectorConfig(multiline=False, type=TextSelectorType.EMAIL)
#                 ),
#                 vol.Required(CONF_PASSWORD, default=password): TextSelector(
#                     TextSelectorConfig(multiline=False, type=TextSelectorType.PASSWORD)
#                 ),
#             }
#         )
#         if user_input is None:
#             return self.async_show_form(step_id="init", data_schema=schema)

#         api = OctopusSpain(user_input[CONF_EMAIL], user_input[CONF_PASSWORD])
#         if await api.login():
#             return self.async_create_entry(data=user_input, title="Octopus Spain")
#         else:
#             return self.async_show_form(step_id="init", data_schema=SCHEMA, errors={'base': 'invalid_auth'})

