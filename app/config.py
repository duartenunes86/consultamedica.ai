from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-5-20250929"
    chroma_persist_dir: str = "./data/chroma_db"
    medical_knowledge_dir: str = "./data/medical_knowledge"

    allowed_origins: list[str] = ["http://localhost:5173"]

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
