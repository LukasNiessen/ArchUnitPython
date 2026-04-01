"""BAD: API layer directly accessing retrieval layer, bypassing services.

This is an intentional architecture violation for demonstration.
The API layer should only talk to the services layer, never directly
to retrieval or LLM.
"""

from retrieval.vector_store import VectorStore
from retrieval.embedder import Embedder


def quick_search(text: str) -> list[dict]:
    """A 'shortcut' endpoint that bypasses the service layer.

    This violates the layered architecture by reaching directly
    into the retrieval layer from the API layer.
    """
    embedder = Embedder()
    store = VectorStore()
    embedding = embedder.embed(text)
    results = store.search(embedding, top_k=3)
    return [{"text": r.text, "score": r.score} for r in results]
