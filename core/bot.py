import asyncio
import logging
import os
import sys
import shutil
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from dotenv import load_dotenv
from core.orchestrator import Orchestrator

# Load environment variables
load_dotenv()

# Configuration
TOKEN = os.getenv("TG_BOT_TOKEN")
ALLOWED_IDS = os.getenv("ALLOWED_CHAT_IDS", "").split(",")

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/bot.log")
    ]
)
logger = logging.getLogger(__name__)

# Initialize Bot, Dispatcher, and Orchestrator
dp = Dispatcher()
bot = None
orchestrator = None

def is_allowed(user_id: int) -> bool:
    # Simple whitelist check
    return str(user_id) in ALLOWED_IDS

@dp.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    if not is_allowed(message.from_user.id):
        logger.warning(f"Unauthorized access attempt from {message.from_user.id}")
        return
    
    await message.answer(f"Hello, {message.from_user.full_name}! Hearth is online. I'm listening.")

@dp.message(F.voice)
async def voice_handler(message: types.Message) -> None:
    if not is_allowed(message.from_user.id):
        return

    wait_msg = await message.answer("🎧 Listening...")
    
    try:
        # Download voice file
        file_id = message.voice.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        
        # Save locally
        local_filename = f"temp_{file_id}.ogg"
        await bot.download_file(file_path, local_filename)
        
        # Process
        response_text = await orchestrator.process(
            user_id=str(message.from_user.id),
            voice_file=local_filename
        )
        
        # Cleanup
        if os.path.exists(local_filename):
            os.remove(local_filename)
            
        await wait_msg.edit_text(response_text)
        
    except Exception as e:
        logger.error(f"Voice Error: {e}")
        await wait_msg.edit_text("Sorry, I couldn't process that audio.")

@dp.message()
async def main_handler(message: types.Message) -> None:
    if not is_allowed(message.from_user.id):
        return

    # User feedback for processing (optional, good for slow Pi)
    # await bot.send_chat_action(message.chat.id, action="typing")

    response = await orchestrator.process(
        user_id=str(message.from_user.id),
        text=message.text
    )
    await message.answer(response)

async def main() -> None:
    global bot, orchestrator
    if not TOKEN:
        logger.error("TG_BOT_TOKEN is not set in .env")
        sys.exit(1)
        
    bot = Bot(token=TOKEN)
    orchestrator = Orchestrator()
    
    logger.info("Starting Hearth Bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
