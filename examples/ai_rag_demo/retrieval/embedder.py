"""Mock embedding service."""

import hashlib

from shared.config import Config


class Embedder:
    """Generates mock embeddings for text chunks."""

    def __init__(self):
        self.model = Config.EMBEDDING_MODEL
        self.dim = Config.EMBEDDING_DIM

    def embed(self, text: str) -> list[float]:
        """Generate a deterministic mock embedding from text."""
        digest = hashlib.sha256(text.encode()).hexdigest()
        values = [int(digest[i : i + 2], 16) / 255.0 for i in range(0, min(len(digest), self.dim * 2), 2)]
        return values[:self.dim] + [0.0] * max(0, self.dim - len(values))

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]
