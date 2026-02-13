import chromadb
from chromadb.utils import embedding_functions
import logging
import os

logger = logging.getLogger(__name__)

# Persistent Data Path
DB_PATH = "/app/hearth_data/chroma"

class MemoryService:
    def __init__(self):
        self.client = None
        self.collection = None
        self.init_db()

    def init_db(self):
        try:
            # Ensure path exists
            os.makedirs(DB_PATH, exist_ok=True)
            
            # Using HuggingFace Embeddings (runs locally in simple python process)
            ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            
            self.client = chromadb.PersistentClient(path=DB_PATH)
            
            self.collection = self.client.get_or_create_collection(
                name="hearth_facts",
                embedding_function=ef
            )
            logger.info(f"🧠 Memory System Initialized at {DB_PATH}")
        except Exception as e:
            logger.error(f"❌ Memory Init Failed: {e}")

    def save_fact(self, text: str, meta: dict = None) -> bool:
        """Store a fact in long-term memory."""
        if not self.collection: return False
        try:
            import uuid
            # Metadata can include 'source', 'user', 'timestamp'
            if meta is None: meta = {}
            if "timestamp" not in meta:
                from datetime import datetime
                meta["timestamp"] = datetime.now().isoformat()
            
            self.collection.add(
                documents=[text],
                metadatas=[meta],
                ids=[str(uuid.uuid4())]
            )
            logger.info(f"🧠 Remembered: {text}")
            return True
        except Exception as e:
            logger.error(f"Save Fact Error: {e}")
            return False

    def query_facts(self, query_text: str, n_results: int = 3) -> str:
        """Semantic search for facts."""
        if not self.collection: return "Memory Offline."
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            # Formatting results
            facts = results['documents'][0]
            if not facts:
                return "No relevant memories found."
            
            return "\n".join([f"- {fact}" for fact in facts])
        except Exception as e:
             logger.error(f"Query Error: {e}")
             return "Error accessing memory."

# Singleton Instance
memory = MemoryService()
