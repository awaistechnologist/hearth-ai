from aiogram import Router, F, types
from services.ai import ask_llm
from services.tools import execute_tool # We can reuse this or import DDGS
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "deny_search")
async def deny_search(callback: types.CallbackQuery):
    await callback.message.edit_text("❌ Search denied.")
    await callback.answer()

@router.callback_query(F.data.startswith("ok_search:"))
async def approve_search(callback: types.CallbackQuery):
    query = callback.data.split(":", 1)[1]
    
    await callback.message.edit_text(f"🔍 Searching for: {query}...")
    
    # 1. Execute Search Manually
    # We call the tool function directly or via execute_tool logic
    from duckduckgo_search import DDGS
    try:
        results = DDGS().text(query, max_results=3)
        search_result = str(results)
    except Exception as e:
        search_result = f"Error: {e}"
        
    # 2. Feed to LLM
    # We construct a prompt that includes the context
    system_prompt = (
        "You requested a web search and the user approved it.\n"
        f"Search Query: {query}\n"
        f"Search Results: {search_result}\n"
        "Please answer the user's original intent based on these results."
    )
    
    # We don't have the original user message text here easily (stateless).
    # But usually the query IS the intent.
    
    response = await ask_llm("Summarize the results.", system_prompt=system_prompt)
    
    await callback.message.answer(response)
    await callback.answer()
