import logging
from services import hass

logger = logging.getLogger(__name__)

# 1. Tool Definitions (Schema)
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": "Fetch calendar events for a specific date range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD"}
                },
                "required": ["start_date", "end_date"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_home",
            "description": "Check the status of devices in the house (lights, sensors, switches, printers, locks, vehicles, etc). Use this before controlling a device to get its entity_id.",
            "parameters": {
                "type": "object",
                "properties": {}
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "control_device",
            "description": "Turn a device on/off or call a service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "description": "e.g. light, switch, cover"},
                    "service": {"type": "string", "description": "e.g. turn_on, turn_off, toggle"},
                    "entity_id": {"type": "string", "description": "The specific entity_id found via check_home (e.g. light.kitchen)"}
                },
                "required": ["domain", "service", "entity_id"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the internet for up-to-date information.",
            "parameters": {
                "type": "object",
                "properties": {
                   "query": {"type": "string", "description": "The search query."},
                   "approved": {"type": "boolean", "description": "Set to True if user explicitly agreed to search."}
                },
                "required": ["query"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remember_fact",
            "description": "Store important information in long-term memory (e.g. user preferences, codes, locations, relationships). Do not use for temporary conversation context.",
            "parameters": {
                "type": "object",
                "properties": {
                   "fact": {"type": "string", "description": "The information to remember."}
                },
                "required": ["fact"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": "Search long-term memory for facts.",
            "parameters": {
                "type": "object",
                "properties": {
                   "query": {"type": "string", "description": "What are you looking for?"}
                },
                "required": ["query"]
            },
        },
    }
]

# 2. Execution Logic
async def execute_tool(tool_call):
    # Support both Ollama (dict) and Gemini (object) formats
    if isinstance(tool_call, dict):
        func_data = tool_call.get("function", {})
        name = func_data.get("name")
        args = func_data.get("arguments", {})
    else:
        name = "unknown"
        args = {}

    logger.info(f"🛠️ Executing Tool: {name} with args {args}")

    # Tool Dispatcher
    if name == "get_calendar_events":
        # ... (Same as before, simplified for brevity but logic remains)
        import json
        if isinstance(args, str):
             try: args = json.loads(args)
             except: pass
        return await hass.get_events_range(args.get("start_date"), args.get("end_date"))

    elif name == "check_home":
        return await hass.get_dashboard_status()
    
    elif name == "control_device":
        import json
        if isinstance(args, str):
             try: args = json.loads(args)
             except: pass
        return await hass.call_action(args.get("domain"), args.get("service"), args.get("entity_id"))

    elif name == "web_search":
        import os
        from duckduckgo_search import DDGS
        import json
        if isinstance(args, str):
             try: args = json.loads(args)
             except: pass
        
        # Check Authorization
        req_confirm = os.getenv("REQUIRE_SEARCH_CONFIRM", "false").lower() == "true"
        # If we have a 'force' flag (from user approval), skip check.
        # But 'args' comes from LLM. LLM can't cheat unless it knows to send 'force=True'.
        # We can implement a special logic: if args contains 'approved=True' (injected by system), proceed.
        # But for now, let's return a special string.
        
        if req_confirm and not args.get("approved"):
            # Return special signal to be caught by ai.py/chat.py
            return f"__REQ_PERM__:{query}"

        query = args.get("query")
         
        try:
            # Use sync DDGS in async context (blocking, but fast enough for minimal use)
            # or run in executor if needed.
            results = DDGS().text(query, max_results=3)
            return str(results)
        except Exception as e:
            return f"Search Failed: {e}"

    elif name == "remember_fact":
        from services.memory import memory
        import json
        if isinstance(args, str):
             try: args = json.loads(args)
             except: pass
        success = memory.save_fact(args.get("fact"))
        return "Fact saved to memory." if success else "Failed to save fact."

    elif name == "search_memory":
        from services.memory import memory
        import json
        if isinstance(args, str):
             try: args = json.loads(args)
             except: pass
        return memory.query_facts(args.get("query"))

    return "Error: Tool not found."
