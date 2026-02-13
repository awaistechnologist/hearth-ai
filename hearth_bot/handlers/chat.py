from services.ai import ask_llm
from database import get_config
from aiogram import Router, types
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message()
async def chat_handler(message: types.Message):
    """General AI Chat Handler"""
    user_id = message.from_user.id
    from database import is_user_allowed
    
    if not await is_user_allowed(user_id):
        if message.chat.type == "private":
            await message.reply("⛔ Access Denied. Ask the admin to approve you.")
        return

    user_text = message.text or ""
    
    # Context Loading
    fam_name = await get_config("family_name") or "Family"
    parents = await get_config("parents") or "Parents"
    
    from datetime import datetime
    now_str = datetime.now().strftime("%Y-%m-%d %A")

    # System Prompt Construction
    system_prompt = (
        f"You are Hearth, a helpful AI assistant for the {fam_name}.\n"
        f"The parents are {parents}.\n"
        f"Current Date: {now_str}.\n"
        "Your goal is to be helpful, concise, and polite.\n"
        "You have access to Long-Term Memory tools: 'remember_fact' and 'search_memory'.\n"
        "- If the user tells you a fact (e.g. 'My gate code is 1234'), use 'remember_fact'.\n"
        "- If asked a question you might know from the past, use 'search_memory'.\n"
        "You also have access to the Internet via 'web_search' tool. Use it for current events/news.\n"
        "If asked about the house or calendar, use the tools provided.\n"
        "IMPORTANT: When asked for 'this week', calculate start_date=today and end_date=today+7 days.\n"
        "When asked for 'tomorrow', use date+1.\n"
        "Do not hallucinate calendar events."
    )
    
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # Call AI (Agentic)
    response = await ask_llm(user_text, system_prompt=system_prompt)
    
    # Check for Permission Request
    if response.startswith("__REQ_PERM__"):
        query = response.split(":", 1)[1]
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        # Callback data length limit is 64 bytes! Truncate query.
        # Format: "ok_search:<query>"
        safe_query = query[:40] 
        builder.button(text="✅ Allow", callback_data=f"ok_search:{safe_query}")
        builder.button(text="❌ Deny", callback_data="deny_search")
        
        await message.reply(f"🔒 I need permission to search for: \n`{query}`", reply_markup=builder.as_markup())
        return

    await message.reply(response)
