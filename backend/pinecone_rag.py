import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

# Get variables from your .env file
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX")

class PineconeRAG:
    def __init__(self):
        from pinecone import Pinecone
        from langchain_huggingface import HuggingFaceEmbeddings
        
        if not PINECONE_API_KEY:
             raise ValueError("PINECONE_API_KEY is missing. Check your .env file.")
             
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.index = self.pc.Index(INDEX_NAME)
        # Using the model that requires 384 dimensions
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    def upsert_chunks(self, texts: List[str]):
        """Embeds and uploads a list of strings to Pinecone."""
        # 1. Create embeddings (384-dimensional vectors)
        embeddings = self.embeddings.embed_documents(texts)
        
        # 2. Prepare the data for Pinecone
        vectors = []
        for i, (text, vector) in enumerate(zip(texts, embeddings)):
            # Generate a unique ID for each chunk
            vector_id = f"vec_{os.urandom(4).hex()}_{i}" 
            vectors.append({
                "id": vector_id,
                "values": vector,
                "metadata": {"content": text}
            })
        
        # 3. Upload to your cloud index
        self.index.upsert(vectors=vectors)

    def search(self, query: str, k: int = 3) -> List[Dict]:
        """Queries the index and returns the top k results."""
        query_embedding = self.embeddings.embed_query(query)
        result = self.index.query(vector=query_embedding, top_k=k, include_metadata=True)
        matches = result.get("matches", [])
        return [{"content": m["metadata"].get("content", ""), "score": m.get("score", 0.0)} 
                for m in matches if m.get("metadata", {}).get("content")]