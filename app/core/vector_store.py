import faiss
import json
import numpy as np
from pathlib import Path

# 📁 Root REAL del proyecto
BASE_DIR = Path(__file__).resolve().parents[2]
CLIENTS_DIR = BASE_DIR / "clients"

# 🧠 Cache en memoria
_vector_cache = {}



def _get_client_paths(client_id: str):
    client_path = CLIENTS_DIR / client_id
    vector_path = client_path / "vector_store"

    index_path = vector_path / "index.faiss"
    meta_path = vector_path / "metadata.json"

    if not index_path.exists():
        raise ValueError(f"No existe index.faiss para cliente '{client_id}'")

    return index_path, meta_path


def save_index(client_id: str, vectors):
    index_path, meta_path = _get_client_paths(client_id)

    embeddings = np.array(
        [v["embedding"] for v in vectors],
        dtype="float32"
    )

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

    print(f"✅ Index guardado para cliente '{client_id}'")
    print("📍 Path:", index_path)


def load_index(client_id: str):
    if client_id in _vector_cache:
        return _vector_cache[client_id]

    index_path, meta_path = _get_client_paths(client_id)

    index = faiss.read_index(str(index_path))

    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    _vector_cache[client_id] = (index, metadata)

    return index, metadata
