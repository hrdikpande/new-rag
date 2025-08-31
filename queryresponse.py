import torch
import numpy as np
import google.generativeai as genai
from chromadb import PersistentClient
import chromadb.utils.embedding_functions as embedding_functions
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# ------------------ Config ------------------
# Load configuration from environment variables
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

# Check if collection exists before trying to get it
try:
    collection = client.get_collection(name=collection_name, embedding_function=google_ef)
    # Check if collection has any data
    collection_count = collection.count()
    if collection_count == 0:
        print(f"⚠️ Warning: Collection '{collection_name}' exists but is empty")
        print("Please run embedding.py first to populate the database")
        exit(1)
    print(f"✅ Connected to collection '{collection_name}' with {collection_count} documents")
except Exception as e:
    print(f"❌ Error: Collection '{collection_name}' not found")
    print("Please run embedding.py first to create and populate the database")
    print(f"Error details: {e}")
    exit(1)

# ------------------ Retrieve + Rerank ------------------
def retrieve_and_rerank(query, top_k=20):
    query_embedding = google_ef([query])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "embeddings"]
    )

    query_tensor = torch.tensor(np.array(query_embedding, dtype=np.float32))
    scored_chunks = []

    for doc, metadata, embedding in zip(results["documents"][0],
                                        results["metadatas"][0],
                                        results["embeddings"][0]):

        emb_tensor = torch.tensor(np.array(embedding, dtype=np.float32))
        score = torch.nn.functional.cosine_similarity(query_tensor, emb_tensor, dim=0).item()

        scored_chunks.append(({
            "document": doc,
            "metadata": metadata,
            "embedding": embedding
        }, score))

    scored_chunks.sort(key=lambda x: x[1], reverse=True)

    # Debug preview
    print("\n--- Top 3 Ranked Chunks ---")
    for i, (chunk, score) in enumerate(scored_chunks[:3], 1):
        print(f"\nRank {i} | Score: {score:.4f}")
        print(f"Source: {chunk['metadata'].get('source', 'unknown')}")
        print(f"Preview: {chunk['document'][:200]}...")
        print("-" * 60)

    return scored_chunks

# ------------------ Prompt Construction ------------------
def build_prompt(context_chunks, query, history=""):
    context = "\n\n---\n\n".join(context_chunks)
    return f"""
You are a knowledgeable assistant.

Conversation history:
{history}

Context:
\"\"\"
{context}
\"\"\"

Question: {query}

Instructions:
- Do NOT mention that the answer is based on the provided context.
- If the context lacks the answer, give your best informed response.

Answer:
"""

# ------------------ LLM Parsing (Gemini) ------------------
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

def llm_parsing(text):
    response = model.generate_content(text)
    return response.text

# ------------------ Main Loop ------------------
if __name__ == "__main__":
    print("💬 Site-RAG Bot ready! (type 'exit' to quit)\n")
    history = ""

    while True:
        query = input("You: ").strip()
        if query.lower() in ["exit", "quit", "bye"]:
            print("👋 Goodbye!")
            break

        top_chunks = retrieve_and_rerank(query)
        top_contexts = [top_chunks[i][0]['document'] for i in range(min(3, len(top_chunks)))]
        prompt = build_prompt(top_contexts, query, history)

        response = llm_parsing(prompt)
        print(f"\n🤖 Bot: {response}\n")

        # Append to history
        history += f"\nYou: {query}\nBot: {response}\n"
