import logging
import os
import datetime
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.tools import DuckDuckGoSearchRun
from core.llm import get_local_llm, get_cloud_llm
from core.memory import MemorySystem
from core.audio import AudioManager

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        self.memory = MemorySystem() # Initializes Chroma
        self.audio = AudioManager()
        try:
            self.search_tool = DuckDuckGoSearchRun()
        except ImportError:
            logger.warning("DuckDuckGoSearchRun failed to initialize. Web search will be disabled.")
            self.search_tool = None
        except Exception as e:
            logger.error(f"Search tool init error: {e}")
            self.search_tool = None
        
        # Ensure log directory exists
        os.makedirs("logs", exist_ok=True)

    def log_interaction(self, user: str, prompt: str, response: str, routing: str):
        """
        Audit log as per Spec Section 5.
        """
        timestamp = datetime.datetime.now().isoformat()
        log_entry = f"[{timestamp}] USER={user} ROUTE={routing}\nPROMPT: {prompt}\nRESPONSE: {response}\n{'-'*40}\n"
        with open("logs/audit.log", "a") as f:
            f.write(log_entry)

    async def process(self, user_id: str, user_name: str = "User", text: str = None, voice_file: str = None) -> str:
        """
        Main Agent Loop.
        """
        # 1. Input Processing
        prompt_text = text
        if voice_file:
            logger.info(f"Processing voice file from {user_name} ({user_id})")
            try:
                transcription = self.audio.transcribe(voice_file)
                prompt_text = transcription
                logger.info(f"Transcribed: {prompt_text}")
            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                return "I had trouble listening to that audio."
        
        if not prompt_text:
            return "I didn't catch that."

        # 2. Memory Retrieval (RAG)
        # Search for relevant facts to inject
        facts = self.memory.search_facts(prompt_text)
        context_str = "\n".join(facts) if facts else "No specific request-related facts found."

        # 3. Routing Logic (Voice-Friendly Triggers)
        route = "LOCAL"
        llm = get_local_llm()
        
        lower_prompt = prompt_text.lower()

        # Cloud Intent: "/cloud" OR "ask the cloud"
        if prompt_text.startswith(("/cloud", "/gpt")) or "ask the cloud" in lower_prompt:
            route = "CLOUD"
            llm = get_cloud_llm()
            # fallback if cloud not configured
            if not llm:
                route = "LOCAL (Fallback)"
                llm = get_local_llm()
            else:
                prompt_text = prompt_text.replace("/cloud", "").replace("/gpt", "").replace("ask the cloud", "").strip()

        # Web Intent: "/web" OR "search for" (explicit request)
        if "/web" in prompt_text or "search for" in lower_prompt or "search the web" in lower_prompt:
             # Only enable if enabled
             if self.search_tool:
                 route = "WEB"
                 # Extract query
                 query = prompt_text.replace("/web", "").replace("search for", "").replace("search the web", "").strip()
                 try:
                     search_results = self.search_tool.run(query)
                     context_str += f"\n\nSearch Results for '{query}':\n{search_results}"
                 except Exception as e:
                     context_str += f"\n\nSearch failed: {e}"

        # 4. Prompt Assembly
        system_prompt = (
            f"You are Hearth, a warm and helpful family assistant running locally on a Raspberry Pi.\n"
            f"You are speaking with {user_name}.\n"
            "You have access to the following family context:\n"
            f"{context_str}\n\n"
            "Answer the user's request concisely and warmly. "
            "If the info isn't in context and you don't know, say so."
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt_text)
        ]

        # 5. Execution
        try:
            logger.info(f"Invoking {route} with prompt: {prompt_text[:50]}...")
            response = llm.invoke(messages)
            response_text = response.content
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            response_text = "I'm having trouble thinking right now (LLM Error)."

        # 6. Logging & Learning
        if prompt_text.startswith("/remember") or "remember that" in lower_prompt:
            # Simple heuristic extraction
            fact_to_save = prompt_text.replace("/remember", "").replace("remember that", "").strip()
            self.memory.add_fact(fact_to_save, user_id)
            response_text = f"I've remembered: {fact_to_save}"

        self.log_interaction(f"{user_name} ({user_id})", prompt_text, response_text, route)
        return response_text
