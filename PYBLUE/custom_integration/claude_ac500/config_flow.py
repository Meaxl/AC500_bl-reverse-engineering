"""Config flow for Soehnle Airfresh Clean Connect 500."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_ADDRESS, CONF_NAME

from .const import DOMAIN


class SoehnleAC500ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_ADDRESS].upper())
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, "Soehnle AC500"),
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS, default="48:87:2D:1F:DB:EB"): str,
                vol.Optional(CONF_NAME, default="Soehnle Airfresh AC500"): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
