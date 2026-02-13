import os
import logging
import asyncio
import aiohttp
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.enums import ChatType
from dotenv import load_dotenv

# Load Environment
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434/api/chat")
MODEL = "llama3.2"

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Init Bot
dp = Dispatcher()
bot = Bot(token=TOKEN)

async def query_ollama(prompt: str, context: list = None) -> str:
    """Send prompt to Local AI."""
    async with aiohttp.ClientSession() as session:
        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        try:
            async with session.post(OLLAMA_URL, json=payload, timeout=60) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("message", {}).get("content", "I am confused.")
                else:
                    return f"Error: Brain error {resp.status}"
        except Exception as e:
            logger.error(f"Ollama Error: {e}")
            return "Thinking failed. Is my brain (Ollama) on?"

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(f"Hello! I am Hearth, your family assistant.\nRunning locally on Raspberry Pi.\nID: {message.from_user.id}")

@dp.message()
async def handle_message(message: types.Message):
    user = message.from_user
    chat_type = message.chat.type
    text = message.text or ""
    
    logger.info(f"Incoming message from User: {user.id} ({user.full_name}) - Text: {text}")
    
    # 1. Privacy / Security Gate
    # In V1, we strictly only talk to the Admin to prevent abuse.
    # Later we can add a "Family Member List". 
    if user.id != ADMIN_ID:
        # If in a group, ignore. If private, politely decline (or ignore).
        if chat_type == ChatType.PRIVATE:
            await message.answer("🔒 Access Denied. You are not the admin.")
        return

    # 2. Group Chat Logic: Only reply if mentioned or replied-to
    bot_info = await bot.get_me()
    is_mentioned = f"@{bot_info.username}" in text
    is_reply = (message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id)
    is_private = (chat_type == ChatType.PRIVATE)

    if not (is_private or is_mentioned or is_reply):
        return  # Ignore ambient chatter

    # 3. Processing
    # Remove mention from text to clean prompt
    clean_text = text.replace(f"@{bot_info.username}", "").strip()
    
    if not clean_text:
        return # Empty message

    # Show "Typing..."
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # 4. Ask Integrator (Concept) -> For now, direct to Ollama
    response = await query_ollama(clean_text)
    
    # 5. Reply
    await message.reply(response)

async def main():
    logger.info("Starting Hearth Bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
