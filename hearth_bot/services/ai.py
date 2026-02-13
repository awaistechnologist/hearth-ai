import aiohttp
import os
import logging
import google.generativeai as genai
from services.tools import TOOLS_SCHEMA, execute_tool

logger = logging.getLogger(__name__)

# Config
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if AI_PROVIDER == "gemini" and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

async def ask_llm(user_text: str, system_prompt: str = None, chat_history: list = None) -> str:
    if AI_PROVIDER == "gemini":
        return await ask_gemini(user_text, system_prompt)
    else:
        return await ask_ollama(user_text, system_prompt)

async def ask_gemini(user_text: str, system_prompt: str = None) -> str:
    try:
        # Debug Mode: Try minimal text generation first to prove connectivity
        # switching to 2.0-flash-001 (Stable) to hopefully avoid the 20/day limit of 2.5
        model_name = "models/gemini-2.0-flash-001" 
        
        # Tools: Updated for arguments
        tool_config = {
            "function_declarations": [
                {
                    "name": "get_calendar_events",
                    "description": "Fetch upcoming events from the family calendar.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "start_date": {"type": "STRING", "description": "YYYY-MM-DD"},
                            "end_date": {"type": "STRING", "description": "YYYY-MM-DD"}
                        },
                        "required": ["start_date", "end_date"]
                    }
                },
                {
                    "name": "check_home",
                    "description": "Check the status of devices in the house (lights, sensors, switches, printers, locks, vehicles, etc).",
                    "parameters": {
                        "type": "OBJECT", "properties": {}
                    }
                },
                {
                    "name": "control_device",
                    "description": "Turn a device on/off or call a service.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "domain": {"type": "STRING", "description": "e.g. light"},
                            "service": {"type": "STRING", "description": "e.g. turn_on"},
                            "entity_id": {"type": "STRING", "description": "e.g. light.kitchen"}
                        },
                        "required": ["domain", "service", "entity_id"]
                    }
                }
            ]
        }

        # Inject System Prompt + Date here to ensure it is seen
        if system_prompt:
             full_prompt = f"{system_prompt}\n\nUser Query: {user_text}"
        else:
             from datetime import datetime
             now_str = datetime.now().strftime("%Y-%m-%d")
             full_prompt = f"System: Today is {now_str}.\n\nUser Query: {user_text}"
        
        logger.info(f"📤 Sending to Gemini: {full_prompt[:100]}...")

        model = genai.GenerativeModel(
            model_name=model_name,
            # system_instruction=system_prompt, # Disabled to avoid SDK ambiguity
            tools=[tool_config] 
        )
        
        chat = model.start_chat(enable_automatic_function_calling=False)
        
        response = await chat.send_message_async(full_prompt)
        
        # Handle Function Call
        if response.parts:
            for part in response.parts:
                if fn := part.function_call:
                    logger.info(f"Gemini requested tool: {fn.name} with args {fn.args}")
                    
                    # Generic Argument Extraction
                    args_dict = {}
                    if fn.args:
                        # Convert Proto Map to dict
                        for key in fn.args:
                            args_dict[key] = fn.args[key]
                    
                    tool_call_obj = {
                        "function": {
                            "name": fn.name,
                            "arguments": args_dict
                        }
                    }
                    
                    result = await execute_tool(tool_call_obj)
                    
                    follow_up = f"Tool Result for {fn.name}:\n{result}\n\nPlease summarize this for the user."
                    response = await chat.send_message_async(follow_up)
                    return response.text

        return response.text
    except Exception as e:
        logger.error(f"Gemini Error: {e}")
        return f"Gemini Error: {e}"

# --- OLLAMA IMPLEMENTATION ---
async def ask_ollama(user_text: str, system_prompt: str = None) -> str:
    # ... (Same as before) ...
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_text})

    async with aiohttp.ClientSession() as session:
        response = await _ollama_call(session, messages, tools=TOOLS_SCHEMA)
        
        if response.get("tool_calls"):
            tool_calls = response["tool_calls"]
            messages.append(response) 
            for tool in tool_calls:
                result = await execute_tool(tool)
                
                # Intercept Permission Request
                if isinstance(result, str) and result.startswith("__REQ_PERM__"):
                    return result
                
                messages.append({
                    "role": "tool",
                    "content": str(result),
                })
            final = await _ollama_call(session, messages)
            return final.get("content", "Startled silence.")

        return response.get("content", "I am confused.")

async def _ollama_call(session, messages, tools=None):
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False
    }
    if tools:
        payload["tools"] = tools

    try:
        async with session.post(OLLAMA_URL, json=payload, timeout=120) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("message", {})
            return {"content": "Brain Error."}
    except:
        return {"content": "Brain Offline."}
