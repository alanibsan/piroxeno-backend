import json
from pathlib import Path
from openai import OpenAI
import tiktoken
from app.core.vector_store import save_index

# ---------- Config ----------
DATA_PATH = Path("data")
EMBED_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100
BATCH_SIZE = 100

client = OpenAI()
encoder = tiktoken.get_encoding("cl100k_base")

# ---------- Load ----------
def load_documents():
    documents = []
    for file in DATA_PATH.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            documents.append(json.load(f))
    return documents

# ---------- Clean ----------
def clean_text(text: str) -> str:
    blacklist = [
        "Esta dirección de correo electrónico está siendo protegida contra los robots de spam.",
        "Necesita tener JavaScript habilitado para poder verlo."
    ]
    for b in blacklist:
        text = text.replace(b, "")
    return " ".join(text.split()).strip()

# ---------- Chunk ----------
def chunk_text(text: str):
    tokens = encoder.encode(text)
    chunks = []

    start = 0
    while start < len(tokens):
        end = start + CHUNK_SIZE
        chunk_tokens = tokens[start:end]
        chunk = encoder.decode(chunk_tokens)

        if len(chunk) > 200:
            chunks.append(chunk)

        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks

# ---------- Enrich ----------
def build_chunks(document):
    text = clean_text(document["content"])
    chunks = chunk_text(text)

    enriched = []
    for i, chunk in enumerate(chunks):
        enriched.append({
            "id": f'{document["hash"]}_{i}',
            "text": chunk,
            "url": document["url"],
            "title": document.get("title", ""),
            "source": document.get("source", ""),
            "section": document.get("section", "")
        })
    return enriched

# ---------- Embed ----------
def embed_chunks(chunks):
    embedded = []

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [c["text"] for c in batch]

        response = client.embeddings.create(
            model=EMBED_MODEL,
            input=texts
        )

        for chunk, emb in zip(batch, response.data):
            embedded.append({**chunk, "embedding": emb.embedding})

    return embedded

# ---------- Run ----------
if __name__ == "__main__":
    documents = load_documents()

    all_chunks = []
    for doc in documents:
        all_chunks.extend(build_chunks(doc))

    vectors = embed_chunks(all_chunks)
    save_index(vectors)

    print(f"✅ FAISS index creado con {len(vectors)} chunks")
