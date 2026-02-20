from abc import ABC, abstractmethod


class ModelProvider(ABC):
    """Abstract base for LLM providers (Anthropic, Ollama, etc.)."""

    @abstractmethod
    async def structured_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: dict,
        tool_name: str = "medical_analysis",
        max_tokens: int = 2048,
    ) -> dict:
        """Return a dict conforming to output_schema."""
