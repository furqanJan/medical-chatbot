import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone_rag import PineconeRAG 

load_dotenv()

# Path to your PDF
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(BASE_DIR, "..", "data", "WHO_respiratory_syndrome_book.pdf")

def run_upload():
    if not os.path.exists(PDF_PATH):
        print(f"❌ Error: Could not find PDF at {PDF_PATH}")
        return

    print("📄 Loading PDF...")
    loader = PyPDFLoader(PDF_PATH)
    documents = loader.load()

    print("✂️ Splitting into chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(documents)
    chunk_texts = [c.page_content for c in chunks]

    print(f"🚀 Found {len(chunk_texts)} chunks. Starting Pinecone CLOUD upload...")
    rag = PineconeRAG()

    # Upload in batches of 100
    batch_size = 100
    for i in range(0, len(chunk_texts), batch_size):
        batch = chunk_texts[i : i + batch_size]
        rag.upsert_chunks(batch) 
        print(f"✅ Batch {i // batch_size + 1} uploaded to Pinecone!")

    print("🎉 Success! Your Pinecone Dashboard will now show data.")

if __name__ == "__main__":
    run_upload()