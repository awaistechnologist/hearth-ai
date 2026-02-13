import logging
import chromadb
from chromadb.config import Settings
from langchain_ollama import OllamaEmbeddings
import os

logger = logging.getLogger(__name__)

class MemorySystem:
    def __init__(self, persist_path: str = "/app/data/chroma", model_name: str = "nomic-embed-text"):
        """
        Initialize ChromaDB with Ollama Embeddings.
        Start with a 'facts' collection.
        """
        self.client = chromadb.PersistentClient(path=persist_path)
        
        # We use Ollama for embeddings to keep the Python footprint small
        # Ensure 'nomic-embed-text' is pulled in Ollama!
        self.embedding_fn = OllamaEmbeddings(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434"),
            model=model_name
        )
        
        # ChromaDB expects a specific embedding function signature or wrapper
        # We might need a custom wrapper if using raw Chroma client, 
        # but let's stick to raw Chroma for simplicity and control,
        # calling the embedding_fn manually for insertion.
        
        self.collection = self.client.get_or_create_collection(name="family_facts")
        logger.info(f"Memory System initialized at {persist_path}")

    def add_fact(self, text: str, user_id: str = "system"):
        """
        Add a text fact to the vector store.
        """
        # Generate embedding
        vector = self.embedding_fn.embed_query(text)
        
        # Add to DB
        import uuid
        fact_id = str(uuid.uuid4())
        
        self.collection.add(
            ids=[fact_id],
            embeddings=[vector],
            documents=[text],
            metadatas=[{"source": "telegram", "user_id": user_id}]
        )
        logger.info(f"Added fact: {text[:30]}...")

    def search_facts(self, query: str, n_results: int = 3) -> list:
        """
        Retrieve relevant facts.
        """
        vector = self.embedding_fn.embed_query(query)
        
        results = self.collection.query(
            query_embeddings=[vector],
            n_results=n_results
        )
        
        # Flatten results
        found = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                found.append(doc)
        
        return found
