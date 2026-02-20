from abc import ABC, abstractmethod

from app.models.schemas import AgentResponse
from app.providers.base import ModelProvider

MEDICAL_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "analysis": {"type": "string", "description": "Texto detalhado da análise"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1, "description": "Pontuação de confiança"},
        "red_flags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Sinais de alerta ou advertências identificados",
        },
        "recommendations": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Recomendações práticas e acionáveis",
        },
    },
    "required": ["analysis", "confidence", "red_flags", "recommendations"],
}


class BaseAgent(ABC):
    """Base class for all medical AI agents."""

    name: str = "base"
    system_prompt: str = ""

    def __init__(self, provider: ModelProvider):
        self.provider = provider

    @abstractmethod
    def build_prompt(self, message: str, context: dict) -> str:
        """Build the user prompt for this agent."""

    async def analyze(self, message: str, context: dict | None = None) -> AgentResponse:
        context = context or {}
        user_prompt = self.build_prompt(message, context)

        result = await self.provider.structured_completion(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            output_schema=MEDICAL_ANALYSIS_SCHEMA,
            tool_name="medical_analysis",
        )

        return AgentResponse(
            agent_name=self.name,
            analysis=result.get("analysis", "Nenhuma análise disponível"),
            confidence=result.get("confidence", 0.0),
            red_flags=result.get("red_flags", []),
            recommendations=result.get("recommendations", []),
        )
