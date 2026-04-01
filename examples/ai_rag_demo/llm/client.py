"""Mock LLM client."""

from models.query import RetrievalResult
from shared.config import Config


class LLMClient:
    """Mock LLM client that generates fake responses."""

    def __init__(self):
        self.model = Config.LLM_MODEL
        self.max_tokens = Config.LLM_MAX_TOKENS

    def generate(self, prompt: str, context: list[RetrievalResult]) -> tuple[str, int]:
        """Generate a mock response based on the prompt and retrieved context.

        Returns:
            Tuple of (response_text, tokens_used).
        """
        context_text = "\n".join(f"- {r.text[:100]}" for r in context)
        answer = (
            f"Based on {len(context)} retrieved documents, "
            f"here is the answer to '{prompt[:50]}...': "
            f"[Mock LLM response using {self.model}]"
        )
        tokens_used = len(answer.split()) * 2  # rough mock
        return answer, tokens_used
