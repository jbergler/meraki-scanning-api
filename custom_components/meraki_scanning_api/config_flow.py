"""Adds config flow for Blueprint."""
import voluptuous as vol
import logging
import secrets

from homeassistant import config_entries
from homeassistant.core import callback

import voluptuous as vol
import homeassistant.helpers.config_validation as cv


from .const import (  # pylint: disable=unused-import
    CONFIG_ENTRY_SCHEMA,
    CONF_SECRET,
    CONF_VALIDATOR,
    CONF_API_VERSION,
    API_V2,
    DOMAIN,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Meraki Scanning API."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    def __init__(self):
        """Initialize."""
        self.api_version = None
        self.secret = None
        self.validator = None

    async def _show_setup_form(self, user_input=None, errors=None):
        """Show the setup form."""

        if user_input is None:
            user_input = {}

        self.api_version = user_input.get(CONF_API_VERSION, API_V2)
        self.secret = user_input.get(CONF_SECRET, secrets.token_urlsafe(32))
        self.validator = user_input.get(CONF_VALIDATOR, "")

        schema = {
            vol.Required(CONF_API_VERSION, default=self.api_version,): vol.In([API_V2]),
            vol.Required(CONF_SECRET, default=self.secret): str,
            vol.Required(CONF_VALIDATOR, default=self.validator): str,
        }

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(schema), errors=errors or {},
        )

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        _LOGGER.debug("_async_step_user()")
        errors = {}

        if user_input is None:
            _LOGGER.debug("user_input is None")
            return await self._show_setup_form(user_input, errors)

        # Check if already configured
        if self.unique_id is None:
            _LOGGER.debug("uniuqe_id is None)")
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

        return self.async_create_entry(title=DOMAIN, data=user_input)


# class OptionsFlowHandler(config_entries.OptionsFlow):
#     """Blueprint config flow options handler."""

#     def __init__(self, config_entry):
#         """Initialize HACS options flow."""
#         self.config_entry = config_entry
#         self.options = dict(config_entry.options)

#     async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
#         """Manage the options."""
#         return await self.async_step_user()

#     async def async_step_user(self, user_input=None):
#         """Handle a flow initialized by the user."""
#         if user_input is not None:
#             self.options.update(user_input)
#             return await self._update_options()

#         return self.async_show_form(
#             step_id="user",
#             data_schema=vol.Schema(
#                 {
#                     vol.Required(
#                         CONF_SECRET, default=self.options.get(CONF_SECRET, "")
#                     ): str,
#                     vol.Required(
#                         CONF_VALIDATOR, default=self.options.get(CONF_VALIDATOR, "")
#                     ): str,
#                 }
#             ),
#         )

#     async def _update_options(self):
#         """Update config entry options."""
#         return self.async_create_entry(
#             title=self.config_entry.data.get(DOMAIN), data=self.options
#         )
