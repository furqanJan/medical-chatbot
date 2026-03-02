# backend/rag_engine.py
# FAISS local RAG — kept as backup if Pinecone is unavailable.

import os
from typing import List, Dict

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


class RAGEngine:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.db_path = "vectorstore/faiss_index"
        self.hf_cache = "./hf_cache"
        self.vector_db = None
        self._load_or_build()

    def _load_or_build(self):
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            cache_folder=self.hf_cache
        )

        if os.path.exists(self.db_path):
            self.vector_db = FAISS.load_local(
                self.db_path,
                embeddings,
                allow_dangerous_deserialization=True
            )
            print("✅ FAISS loaded from disk")
            return

        print("🔨 Building FAISS index from PDF...")

        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")

        loader = PyPDFLoader(self.pdf_path)
        documents = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100
        )
        chunks = splitter.split_documents(documents)

        self.vector_db = FAISS.from_documents(chunks, embeddings)

        os.makedirs(self.db_path, exist_ok=True)
        self.vector_db.save_local(self.db_path)
        print("💾 FAISS index saved")

    def search(self, query: str, k: int = 3) -> List[Dict]:
        if not self.vector_db:
            return []

        docs = self.vector_db.similarity_search(query, k=k)
        return [
            {"content": doc.page_content, "metadata": doc.metadata}
            for doc in docs
        ]