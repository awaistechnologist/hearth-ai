from aiogram import Router, types
from aiogram.filters import Command
from services import hass
from services.ai import ask_llm
import logging
import json
import re
import asyncio
from datetime import datetime, timedelta

router = Router()
logger = logging.getLogger(__name__)

def extract_json(text):
    """Robust JSON extraction from LLM response"""
    text = text.strip()
    # Try finding first { and last }
    match = re.search(r'(\{.*\})', text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text)

from database import is_user_allowed, approve_user
import os

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

@router.message(Command("id"))
async def id_command(message: types.Message):
    await message.reply(f"Your ID: `{message.from_user.id}`", parse_mode="Markdown")

@router.message(Command("permit"))
async def permit_command(message: types.Message):
    """Allow a user: /permit 123456789"""
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        target_id = int(message.text.split()[1])
        await approve_user(target_id)
        await message.reply(f"✅ User {target_id} approved!")
    except:
        await message.reply("Usage: /permit <user_id>")

@router.message(Command("sleep"))
async def sleep_command(message: types.Message):
    """Trigger Sleep + AI Security Check"""
    if not await is_user_allowed(message.from_user.id):
        return

    logger.info(f"User {message.from_user.id} triggered /sleep")
    status_msg = await message.reply("🧠 AI Analyst starting up...")
    
    try:
        # 1. Get Data
        await status_msg.edit_text("🔍 Scanning home devices (~2s)...")
        dashboard = await hass.get_security_dashboard()
        
        if not dashboard:
            await status_msg.edit_text("⚠️ No security devices found to check (or HA Error).")
             # Proceed to scene anyway?
        else:
            size_kb = len(dashboard) / 1024
            logger.info(f"Dashboard Size: {size_kb:.2f} KB")
            device_count = len(dashboard.splitlines())
            await status_msg.edit_text(f"🧠 Analyzing {device_count} devices... (This takes a moment ⏳)")
            
            # 2. Ask AI
            prompt = (
                "You are a Home Security Analyst.\n"
                "Analyze the provided list of devices.\n"
                "Identify items that are UNSECURED (Unlocked, Open).\n"
                "Ignore 'locked', 'closed', 'off', 'unavailable', or '2' (Mercedes generic code).\n"
                "Return valid JSON: {'unsecured': [{'name': '...', 'entity_id': '...'}]}.\n"
                "If safe, return {'unsecured': []}."
            )
            
            # This call uses Ollama and can be slow
            ai_resp = await ask_llm(dashboard, system_prompt=prompt)
            logger.info(f"AI Response: {ai_resp[:100]}...")
            
            try:
                data = extract_json(ai_resp)
                unsecured = data.get("unsecured", [])
            except Exception as e:
                logger.error(f"JSON Parse Error: {e} | Resp: {ai_resp}")
                await status_msg.edit_text(f"⚠️ AI JSON Error: {e}\nRaw: {ai_resp[:50]}...")
                unsecured = []

            # 3. Act
            if unsecured:
                names = ", ".join([u["name"] for u in unsecured])
                await status_msg.edit_text(f"⚠️ **Security Alert**: {names} are UNSECURED!\n🔒 Securing...")
                
                for item in unsecured:
                    eid = item.get("entity_id", "")
                    if "cover" in eid:
                        await hass.call_action("cover", "close_cover", eid)
                    else:
                        await hass.call_action("lock", "lock", eid)
                
                await asyncio.sleep(2)
                await status_msg.edit_text(f"🔒 Secured {names}.\n😴 Sleeping...")
            else:
                await status_msg.edit_text("✅ Perimeter Secure.\n😴 Sleeping...")

    except Exception as e:
         logger.error(f"Sleep Error: {e}")
         await status_msg.edit_text(f"⚠️ Error during checks: {e}")

    # 4. Activate Scene
    success = await hass.activate_scene("scene.sleep")
    if success:
        await message.answer("😴 Goodnight!")
    else:
        await message.answer("⚠️ Scene activation failed.")

@router.message(Command("morning"))
async def morning_command(message: types.Message):
    """
    Trigger Morning Scene + Show Calendar.
    """
    if not await is_user_allowed(message.from_user.id):
        return
    logger.info(f"User {message.from_user.id} triggered /morning")
    status_msg = await message.reply("☀️ Good morning! Waking up the house...")

    # 1. Activate Scene
    scene_ok = await hass.activate_scene("scene.morning")
    
    # 2. Get Calendar
    today = datetime.now()
    end_of_day = today + timedelta(days=1)
    
    events_str = await hass.get_events_range(
        today.strftime("%Y-%m-%d"), 
        end_of_day.strftime("%Y-%m-%d")
    )
    
    # Format Response
    response = (
        f"☀️ **Morning Protocol**\n"
        f"Scene: {'✅ Active' if scene_ok else '⚠️ Failed (Check HA)'}\n\n"
        f"📅 **Today's Agenda:**\n"
        f"{events_str}"
    )
    
    await status_msg.edit_text(response, parse_mode="Markdown")
