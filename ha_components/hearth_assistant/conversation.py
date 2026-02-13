import logging
import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.components import conversation

from .const import DOMAIN, DEFAULT_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hearth Assistant from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    agent = HearthConversationAgent(hass, entry)
    conversation.async_set_agent(hass, entry, agent)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    conversation.async_unset_agent(hass, entry)
    return True

class HearthConversationAgent(conversation.AbstractConversationAgent):
    """Hearth Conversation Agent."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.history = {}

    @property
    def supported_languages(self) -> list[str]:
        return ["en"]

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence."""
        url = self.entry.data.get(CONF_URL, DEFAULT_URL)
        text = user_input.text
        user_id = user_input.context.user_id or "system"

        # Resolve User Name from Registry
        user_name = "Unknown"
        if user_input.context.user_id:
            user = await self.hass.auth.async_get_user(user_input.context.user_id)
            if user:
                user_name = user.name

        _LOGGER.debug(f"Sending to Hearth ({url}) from {user_name}: {text}")

        # Call the Hearth API
        async with aiohttp.ClientSession() as session:
            try:
                # We send both ID (for strict auth if needed) and Name (for the AI)
                payload = {
                    "user_id": user_input.context.user_id,
                    "user_name": user_name, 
                    "text": text
                }
                async with session.post(url, json=payload, timeout=60) as resp:
                    if resp.status != 200:
                        response_text = f"Error: Brain returned status {resp.status}"
                    else:
                        data = await resp.json()
                        response_text = data.get("response", "No response from brain.")
            except Exception as e:
                _LOGGER.error(f"Failed to connect to Hearth: {e}")
                response_text = "I can't reach my brain right now."

        # Return the result in HA format
        intent_response = conversation.ConversationResult(
            response=conversation.ConversationResponse(
                speech={"plain": {"speech": response_text, "extra_data": None}}
            ),
            conversation_id=user_input.conversation_id,
        )
        return intent_response
