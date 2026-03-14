import faiss
import json
import numpy as np
from pathlib import Path

# 📁 Root del proyecto
BASE_DIR = Path(__file__).resolve().parents[2]
CLIENTS_DIR = BASE_DIR / "clients"

# 🧠 Cache en memoria
_vector_cache = {}


def _get_client_paths(client_id: str):
    client_path = CLIENTS_DIR / client_id
    vector_path = client_path / "vector_store"

    index_path = vector_path / "index.faiss"
    meta_path = vector_path / "metadata.json"

    # Cliente sin vector store → modo prompt-only
    if not index_path.exists():
        print(f"[RAG] client='{client_id}' → prompt-only mode")
        return None, None

    return index_path, meta_path


def save_index(client_id: str, vectors):
    """
    Crea o actualiza el índice FAISS de un cliente.
    """

    vector_path = CLIENTS_DIR / client_id / "vector_store"
    vector_path.mkdir(parents=True, exist_ok=True)

    index_path = vector_path / "index.faiss"
    meta_path = vector_path / "metadata.json"

    embeddings = np.array([v["embedding"] for v in vectors], dtype="float32")

    # normalización para cosine similarity
    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    faiss.write_index(index, str(index_path))

    metadata = []
    for v in vectors:
        item = v.copy()
        item.pop("embedding")
        metadata.append(item)

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # limpiar cache
    if client_id in _vector_cache:
        del _vector_cache[client_id]

    print(f"✅ Index guardado para cliente '{client_id}'")
    print("📍 Path:", index_path)


def load_index(client_id: str):
    """
    Carga el índice FAISS y metadata desde disco.
    Usa cache en memoria para evitar I/O repetido.
    """

    # 🧠 cache hit
    if client_id in _vector_cache:
        return _vector_cache[client_id]

    index_path, meta_path = _get_client_paths(client_id)

    # cliente sin vector store
    if index_path is None:
        _vector_cache[client_id] = (None, None)
        return None, None

    try:
        index = faiss.read_index(str(index_path))

        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        _vector_cache[client_id] = (index, metadata)

        print(f"[RAG] Loaded vector store for '{client_id}'")

        return index, metadata

    except Exception as e:
        print(f"[RAG ERROR] Failed loading index for '{client_id}': {e}")
        return None, None