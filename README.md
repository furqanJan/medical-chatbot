## Medical RAG Chatbot

### Features
- PDF-based Retrieval-Augmented Generation (RAG)
- Semantic search using vector embeddings
- Context memory (conversation window)
- Cache for repeated queries
- Modular LLM layer (pluggable)

### Architecture
User Query → Cache → Context Memory → Vector DB → PDF Chunks → Answer

### Current Mode
- Extractive RAG (PDF-grounded answers)
- LLM layer intentionally disabled due to offline constraints

### Tech Stack
- FastAPI
- LangChain
- HuggingFace embeddings
- FAISS / vector store
- Python 3.11
q