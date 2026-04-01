"""Query and response models."""

from dataclasses import dataclass, field


@dataclass
class Query:
    text: str
    top_k: int = 5
    filters: dict = field(default_factory=dict)


@dataclass
class RetrievalResult:
    text: str
    score: float
    source: str


@dataclass
class RAGResponse:
    answer: str
    sources: list[RetrievalResult]
    model: str
    tokens_used: int
