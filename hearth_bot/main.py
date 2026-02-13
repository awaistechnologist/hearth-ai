import os
import logging
import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from database import init_db
from handlers import onboarding, chat, commands
from aiogram.types import BotCommand

# Load Env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Logic
async def main():
    logging.basicConfig(level=logging.INFO)
    
    # 1. Database
    await init_db()
    from database import approve_user
    if ADMIN_ID > 0:
        await approve_user(ADMIN_ID)
    
    # 2. Init Memory (Downloads Embedding Model if needed)
    from services.memory import memory
    logging.info("Memory Service Ready.")

    # 3. Bot Setup
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    from handlers import onboarding, chat, commands, callbacks
# ...
    # 3. Register Routers
    dp.include_router(onboarding.router)
    dp.include_router(commands.router)
    dp.include_router(callbacks.router)
    dp.include_router(chat.router)
    
    # 4. Global Injection in handlers (Hack for simple V1)
    chat.bot = bot 
    
    # 5. Set Bot Menu Commands
    await bot.set_my_commands([
        BotCommand(command="start", description="Restart Wizard"),
        BotCommand(command="morning", description="Turn on Morning Scene ☀️"),
        BotCommand(command="sleep", description="Activate Sleep Mode 😴"),
        BotCommand(command="id", description="Show My ID 🆔"),
        BotCommand(command="permit", description="Approve User (Admin) 🛡️"),
    ])
    
    logging.info("Hearth Bot V2 Starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
