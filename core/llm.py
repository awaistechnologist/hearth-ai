import os
import logging
from langchain_ollama import ChatOllama
from langchain_community.chat_models import ChatOpenAI

logger = logging.getLogger(__name__)

def get_local_llm(model="llama3.2", temperature=0.7):
    """
    Returns the configured local Ollama instance.
    """
    base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
    logger.info(f"Connecting to Local LLM at {base_url} with model {model}")
    return ChatOllama(
        base_url=base_url,
        model=model,
        temperature=temperature
    )

def get_cloud_llm(temperature=0.7):
    """
    Returns the configured Cloud LLM (OpenAI compatible).
    Requires CLOUD_API_KEY in .env
    """
    api_key = os.getenv("CLOUD_API_KEY")
    if not api_key:
        logger.warning("CLOUD_API_KEY missing. Fallback to local or error.")
        return None
        
    return ChatOpenAI(
        api_key=api_key,
        model="gpt-4o", # Or make configurable
        temperature=temperature
    )
