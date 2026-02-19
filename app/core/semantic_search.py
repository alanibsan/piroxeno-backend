from openai import OpenAI
import numpy as np
import faiss
from app.core.vector_store import load_index

from app.config import settings
client = OpenAI(api_key=settings.openai_api_key)


EMBED_MODEL = "text-embedding-3-small"
SCORE_THRESHOLD = 0.25


def embed_query(query: str):
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=[query]
    )
    return np.array(response.data[0].embedding).astype("float32")


def boost_score(result):
    score = result["score"]

    if result.get("section") == "core":
        score *= 1.15
    elif result.get("section") == "help":
        score *= 1.05
    elif result.get("section") == "blog":
        score *= 0.7

    return score


def search(client_id: str, query: str, top_k: int = 20):
    # 🔥 Ahora multi-tenant
    index, metadata = load_index(client_id)

    query_vector = embed_query(query)

    query_matrix = np.ascontiguousarray(
        query_vector.reshape(1, -1),
        dtype="float32"
    )

    faiss.normalize_L2(query_matrix)

    distances, indices = index.search(query_matrix, top_k)

    results = []
    for score, idx in zip(distances[0], indices[0]):
        if score < SCORE_THRESHOLD:
            continue

        r = {
            **metadata[idx],
            "score": float(score)
        }
        results.append(r)

    if not results:
        return []

    for r in results:
        r["score"] = boost_score(r)

    seen = set()
    unique = []
    for r in results:
        if r["url"] in seen:
            continue
        seen.add(r["url"])
        unique.append(r)

    unique.sort(key=lambda x: x["score"], reverse=True)

    return unique[:5]
