# backend/test_rag.py
# Quick test: run with: python test_rag.py

from pinecone_rag import PineconeRAG

rag = PineconeRAG()

question = "What is the global risk of MERS?"
results = rag.search(question, k=3)

print("\n--- RESULTS ---\n")
for r in results:
    print(f"Score: {r['score']:.4f}")
    print(r["content"])
    print("\n" + "-" * 40 + "\n")