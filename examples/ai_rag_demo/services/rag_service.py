"""RAG orchestration service - the core business logic."""

from llm.client import LLMClient
from models.document import Document
from models.query import Query, RAGResponse
from retrieval.embedder import Embedder
from retrieval.vector_store import VectorStore


class RAGService:
    """Orchestrates the full Retrieval-Augmented Generation pipeline."""

    def __init__(self):
        self.embedder = Embedder()
        self.vector_store = VectorStore()
        self.llm = LLMClient()

    def ingest(self, document: Document) -> int:
        """Ingest a document: chunk, embed, and store."""
        chunks = document.split_into_chunks()
        for chunk in chunks:
            chunk.embedding = self.embedder.embed(chunk.text)
        return self.vector_store.insert(chunks)

    def query(self, query: Query) -> RAGResponse:
        """Execute a RAG query: embed, retrieve, generate."""
        query_embedding = self.embedder.embed(query.text)
        results = self.vector_store.search(query_embedding, top_k=query.top_k)
        answer, tokens = self.llm.generate(query.text, results)

        return RAGResponse(
            answer=answer,
            sources=results,
            model=self.llm.model,
            tokens_used=tokens,
        )
