from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import set_config, get_config
import logging

router = Router()

class ValidStates(StatesGroup):
    waiting_family_name = State()
    waiting_parents = State()
    waiting_validation = State()

@router.message(Command("start"))
async def start_wizard(message: types.Message, state: FSMContext):
    # Security: Only admins can start setup
    import os
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    if message.from_user.id != ADMIN_ID:
        # Check if they are authorized user?
        from database import is_user_allowed
        if not await is_user_allowed(message.from_user.id):
             return # Silent ignore

    # Check if already setup
    family_name = await get_config("family_name")
    if family_name:
        await message.answer(f"Welcome back! {family_name} family system is online.")
        return

    await message.answer(
        "👋 **Welcome to Hearth!**\n\n"
        "I am your new privacy-first family assistant.\n"
        "To get started, I need to know a little bit about who you are.\n\n"
        "First, what is your **Family Name**? (e.g. 'The Smiths' or 'Khan Family')"
    )
    await state.set_state(ValidStates.waiting_family_name)

@router.message(ValidStates.waiting_family_name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    await set_config("family_name", name)
    await message.answer(f"Nice to meet you, **{name}**!\n\nWho are the parents? (Enter names separated by comma)")
    await state.set_state(ValidStates.waiting_parents)

@router.message(ValidStates.waiting_parents)
async def process_parents(message: types.Message, state: FSMContext):
    parents = message.text.strip()
    await set_config("parents", parents)
    await message.answer(
        "Great! Setup is complete for now.\n\n"
        "You can now chat with me normally. Try asking:\n"
        "- 'Help me plan dinner'\n"
        "- 'Add a reminder'"
    )
    await state.clear()
