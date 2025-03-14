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

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from .octopus_spain import OctopusSpain  # Importa tu clase OctopusSpain

class OctopusSpainConfigFlow(config_entries.ConfigFlow):
    """Maneja el flujo de configuración para Octopus Spain."""

    VERSION = 1

    def __init__(self):
        """Inicializa el flujo de configuración."""
        self._email = None
        self._password = None

    async def async_step_user(self, user_input=None):
        """Paso de configuración de usuario."""
        if user_input is not None:
            # Almacena las credenciales proporcionadas
            self._email = user_input[CONF_EMAIL]
            self._password = user_input[CONF_PASSWORD]

            # Realiza alguna acción para verificar las credenciales
            octopus_spain = OctopusSpain(self._email, self._password)
            login_successful = await octopus_spain.login()

            if login_successful:
                return self.async_create_entry(
                    title="Octopus Spain",
                    data={CONF_EMAIL: self._email, CONF_PASSWORD: self._password},
                )
            else:
                return self.async_show_form(
                    step_id="user", errors={"base": "invalid_credentials"}
                )

        # Si no hay datos de usuario, muestra el formulario de entrada
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
            }),
        )