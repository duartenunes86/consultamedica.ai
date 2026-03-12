import logging

import anthropic

from app.config import get_settings
from app.providers.base import ModelProvider

logger = logging.getLogger(__name__)

# Preços Claude Sonnet 4.6 (USD por token)
_COST_INPUT = 3.00 / 1_000_000
_COST_OUTPUT = 15.00 / 1_000_000


class AnthropicProvider(ModelProvider):
    """Wraps the Anthropic API with forced tool_use for structured output."""

    def __init__(self):
        settings = get_settings()
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model

    async def structured_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: dict,
        tool_name: str = "medical_analysis",
        max_tokens: int = 2048,
    ) -> dict:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            tools=[{
                "name": tool_name,
                "description": f"Return structured output for {tool_name}",
                "input_schema": output_schema,
            }],
            tool_choice={"type": "tool", "name": tool_name},
        )

        usage = response.usage
        cost = usage.input_tokens * _COST_INPUT + usage.output_tokens * _COST_OUTPUT
        logger.info(
            "[tokens] tool=%s  in=%d  out=%d  custo=$%.5f",
            tool_name,
            usage.input_tokens,
            usage.output_tokens,
            cost,
        )

        for block in response.content:
            if block.type == "tool_use":
                return block.input

        # Fallback — return text as analysis with zero confidence
        text = response.content[0].text if response.content else "No output"
        return {"analysis": text, "confidence": 0.0, "red_flags": [], "recommendations": []}
