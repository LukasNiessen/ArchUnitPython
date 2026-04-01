"""Document models for the RAG pipeline."""

from dataclasses import dataclass, field

from shared.config import Config


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)
    embedding: list[float] = field(default_factory=list)


@dataclass
class Document:
    id: str
    content: str
    source: str
    chunks: list[Chunk] = field(default_factory=list)

    def split_into_chunks(self) -> list[Chunk]:
        size = Config.CHUNK_SIZE
        overlap = Config.CHUNK_OVERLAP
        text = self.content
        chunks = []
        start = 0
        while start < len(text):
            end = start + size
            chunks.append(Chunk(text=text[start:end], metadata={"source": self.source}))
            start = end - overlap
        self.chunks = chunks
        return chunks
