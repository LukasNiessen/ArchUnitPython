"""Shared configuration for the RAG pipeline."""


class Config:
    EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_DIM = 1536
    LLM_MODEL = "gpt-4"
    LLM_MAX_TOKENS = 2048
    VECTOR_DB_COLLECTION = "documents"
    CHUNK_SIZE = 512
    CHUNK_OVERLAP = 64
    TOP_K = 5

    @staticmethod
    def get_api_key() -> str:
        return "sk-mock-key-for-demo"
