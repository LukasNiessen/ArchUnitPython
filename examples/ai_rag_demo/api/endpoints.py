"""API endpoints for the RAG service (mock FastAPI-style)."""

from models.document import Document
from models.query import Query, RAGResponse
from services.rag_service import RAGService


_rag_service = RAGService()


def ingest_document(doc_id: str, content: str, source: str) -> dict:
    """POST /ingest - Ingest a document into the RAG pipeline."""
    doc = Document(id=doc_id, content=content, source=source)
    count = _rag_service.ingest(doc)
    return {"status": "ok", "chunks_stored": count}


def ask(question: str, top_k: int = 5) -> dict:
    """POST /ask - Ask a question using RAG."""
    query = Query(text=question, top_k=top_k)
    response: RAGResponse = _rag_service.query(query)
    return {
        "answer": response.answer,
        "sources": [{"text": s.text[:100], "score": s.score} for s in response.sources],
        "model": response.model,
        "tokens_used": response.tokens_used,
    }
