from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components import conversation as ha_conversation
from .conversation import HearthConversationAgent
from .const import DOMAIN

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hearth Assistant from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    agent = HearthConversationAgent(hass, entry)
    ha_conversation.async_set_agent(hass, entry, agent)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    ha_conversation.async_unset_agent(hass, entry)
    return True
