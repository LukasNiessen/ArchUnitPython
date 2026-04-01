"""BAD: Shared/utility layer importing from services layer.

This is an intentional architecture violation for demonstration.
The shared layer is the lowest layer and should NEVER depend on
higher layers like services.
"""

from services.rag_service import RAGService


def get_default_service() -> RAGService:
    """A 'convenience' function that creates a leaky dependency.

    This violates the layered architecture because the shared layer
    should not know about the services layer.
    """
    return RAGService()
