from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-6"
    chroma_persist_dir: str = "./data/chroma_db"
    medical_knowledge_dir: str = "./data/medical_knowledge"

    allowed_origins: list[str] = ["*"]

    @property
    def cors_origins(self) -> list[str]:
        # ALLOWED_ORIGINS env var can be comma-separated
        if self.allowed_origins == ["*"]:
            return ["*"]
        expanded = []
        for o in self.allowed_origins:
            for part in o.split(","):
                part = part.strip()
                if part:
                    expanded.append(part)
        return expanded

    # Admin
    admin_api_key: str = ""

    # Stripe payment
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    consultation_price_cents: int = 4999  # R$ 49,99

    # Email / booking settings
    resend_api_key: str = ""
    sender_email: str = "noreply@consultamedica.ai"
    doctor_email: str = ""

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "koesn/llama3-openbiollm-8b"
    agent_providers: dict[str, str] = {
        "triage": "anthropic",
        "diagnosis": "anthropic",
        "treatment": "anthropic",
        "drug_interactions": "anthropic",
        "literature": "anthropic",
        "guidelines": "anthropic",
        "consensus": "anthropic",
    }

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
