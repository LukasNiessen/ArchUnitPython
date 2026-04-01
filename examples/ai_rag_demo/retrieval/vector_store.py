"""Mock vector store for document retrieval."""

from models.document import Chunk
from models.query import RetrievalResult
from shared.config import Config


class VectorStore:
    """In-memory mock vector database."""

    def __init__(self):
        self.collection = Config.VECTOR_DB_COLLECTION
        self._store: list[Chunk] = []

    def insert(self, chunks: list[Chunk]) -> int:
        self._store.extend(chunks)
        return len(chunks)

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[RetrievalResult]:
        """Mock similarity search - returns first top_k chunks."""
        results = []
        for i, chunk in enumerate(self._store[:top_k]):
            results.append(
                RetrievalResult(
                    text=chunk.text,
                    score=1.0 / (i + 1),
                    source=chunk.metadata.get("source", "unknown"),
                )
            )
        return results

    def clear(self) -> None:
        self._store.clear()

    @property
    def count(self) -> int:
        return len(self._store)
