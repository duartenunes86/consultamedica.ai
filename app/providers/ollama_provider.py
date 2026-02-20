import json
import logging
import re

from openai import AsyncOpenAI

from app.config import get_settings
from app.providers.base import ModelProvider

logger = logging.getLogger(__name__)


class OllamaProvider(ModelProvider):
    """Uses Ollama's OpenAI-compatible API for structured output via JSON prompting."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(
            base_url=f"{settings.ollama_base_url}/v1",
            api_key="ollama",  # Ollama doesn't need a real key
        )
        self.model = settings.ollama_model

    async def structured_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: dict,
        tool_name: str = "medical_analysis",
        max_tokens: int = 2048,
    ) -> dict:
        schema_instruction = (
            f"\n\nYou MUST respond with ONLY a valid JSON object matching this schema:\n"
            f"{json.dumps(output_schema, indent=2)}\n"
            f"Do not include any text outside the JSON object."
        )
        augmented_system = system_prompt + schema_instruction

        result = await self._attempt_completion(augmented_system, user_prompt, max_tokens)
        if result is not None:
            return result

        # Retry once with correction prompt
        logger.warning("Ollama JSON parse failed, retrying with correction prompt")
        correction = user_prompt + "\n\nIMPORTANT: Your previous response was not valid JSON. Respond with ONLY a valid JSON object, no other text."
        result = await self._attempt_completion(augmented_system, correction, max_tokens)
        if result is not None:
            return result

        # Final fallback
        logger.error("Ollama JSON parsing failed after retry")
        return {"analysis": "Análise indisponível (erro de leitura)", "confidence": 0.0, "red_flags": [], "recommendations": []}

    async def _attempt_completion(self, system_prompt: str, user_prompt: str, max_tokens: int) -> dict | None:
        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=0.3,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        text = response.choices[0].message.content or ""
        return self._parse_json(text)

    @staticmethod
    def _parse_json(text: str) -> dict | None:
        # Strip markdown code fences if present
        text = text.strip()
        fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
