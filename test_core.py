import asyncio
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TEST")

# Add current dir to path
sys.path.append(os.getcwd())

from core.orchestrator import Orchestrator
from core.audio import AudioManager

async def main():
    print("--- 🧪 HEARTH CORE TEST ---")
    
    # 1. Test Orchestrator Init (Connects to Chroma & Ollama)
    print("\n[1/3] Initializing Orchestrator (Ollama + ChromaDB)...")
    try:
        orch = Orchestrator()
        print("✅ Orchestrator Initialized")
    except Exception as e:
        print(f"❌ Initialization Failed: {e}")
        return

    # 2. Test Rull Loop (Text -> RAG -> LLM)
    print("\n[2/3] Testing 'Process' Loop (Llama 3.2)...")
    try:
        response = await orch.process(user_id="test_user", text="What is this system?")
        print(f"✅ Response received: {response}")
    except Exception as e:
        print(f"❌ Processing Failed: {e}")

    # 3. Test Audio Loading (Faster-Whisper)
    print("\n[3/3] Testing Audio Model Loading...")
    try:
        audio = AudioManager(model_size="base")
        audio.load_model()
        print("✅ Audio Model Loaded")
        audio.unload_model()
        print("✅ Audio Model Unloaded")
    except Exception as e:
        print(f"❌ Audio Test Failed: {e}")

    print("\n--- TEST COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(main())
