import os
import uuid
from chromadb import PersistentClient
import chromadb.utils.embedding_functions as embedding_functions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ------------------ Config ------------------
# Load configuration from environment variables
txt_directory = os.getenv('SCRAPED_PAGES_DIR', './scraped_pages')
chromadb_folder = os.getenv('CHROMADB_DIR', './chromadb')
collection_name = os.getenv('COLLECTION_NAME', 'site_documents')
gemini_api_key = os.getenv('GOOGLE_AI_API_KEY')

if not gemini_api_key:
    print("❌ Error: GOOGLE_AI_API_KEY not found in environment variables")
    print("Please set GOOGLE_AI_API_KEY in your .env file")
    exit(1)

# ------------------ Embedding + Chroma Setup ------------------
google_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(api_key=gemini_api_key)
client = PersistentClient(path=chromadb_folder)

if collection_name not in client.list_collections():
    collection = client.create_collection(name=collection_name, embedding_function=google_ef)
else:
    collection = client.get_collection(name=collection_name, embedding_function=google_ef)
    # optional: clear existing data
    existing_ids = collection.get()["ids"]
    if existing_ids:
        collection.delete(ids=existing_ids)

# ------------------ Helper: chunk text ------------------
def chunk_text(text, chunk_size=None, overlap=None):
    # Get configuration from environment variables
    if chunk_size is None:
        chunk_size = int(os.getenv('CHUNK_SIZE', '1000'))
    if overlap is None:
        overlap = int(os.getenv('CHUNK_OVERLAP', '200'))
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

# ------------------ Process and Store ------------------
# Check if directory exists and has files
if not os.path.exists(txt_directory):
    print(f"❌ Error: Directory '{txt_directory}' does not exist")
    print("Please run scraper.py first to generate scraped content")
    exit(1)

txt_files = [f for f in os.listdir(txt_directory) if f.endswith('.txt')]
if not txt_files:
    print(f"❌ Error: No .txt files found in '{txt_directory}'")
    print("Please run scraper.py first to generate scraped content")
    exit(1)

print(f"📁 Found {len(txt_files)} text files to process")

# Get minimum chunk size once (not in loop)
min_chunk_size = int(os.getenv('MIN_CHUNK_SIZE', '100'))
doc_count = 0

for txt_file in txt_files:
    if not txt_file.endswith(".txt"):
        continue

    txt_path = os.path.join(txt_directory, txt_file)
    with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
        full_text = f.read()

    chunks = chunk_text(full_text)

    for chunk in chunks:
        if len(chunk) < min_chunk_size:  # skip tiny fragments
            continue
        try:
            doc_id = str(uuid.uuid4())
            collection.add(
                ids=[doc_id],
                documents=[chunk],
                metadatas=[{"source": txt_file}]
            )
            doc_count += 1
            print(f"Stored chunk from {txt_file} as ID {doc_id}")
        except Exception as e:
            print(f"⚠️ Failed to store chunk: {e}")

print(f"\n✅ Stored total {doc_count} chunks into Chroma at '{chromadb_folder}'")