import anthropic

from app.config import get_settings
from app.providers.base import ModelProvider


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

        for block in response.content:
            if block.type == "tool_use":
                return block.input

        # Fallback — return text as analysis with zero confidence
        text = response.content[0].text if response.content else "No output"
        return {"analysis": text, "confidence": 0.0, "red_flags": [], "recommendations": []}
