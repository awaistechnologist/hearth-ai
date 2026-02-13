from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import voluptuous as vol
from .const import DOMAIN, CONF_URL, DEFAULT_URL

class HearthConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hearth."""
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="Hearth Family Brain", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_URL, default=DEFAULT_URL): str,
            })
        )
