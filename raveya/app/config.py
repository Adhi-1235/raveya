import os
from functools import lru_cache


class Settings:
    ENVIRONMENT: str
    DATABASE_URL: str
    OPENAI_API_KEY: str | None
    OPENAI_MODEL: str
    AI_MODE: str

    def __init__(self) -> None:
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
        # Default to local SQLite file if not configured
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./raveya.db")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        # "live" calls OpenAI, "mock" uses deterministic mock logic
        self.AI_MODE = os.getenv("AI_MODE", "live").lower()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Cached settings accessor so we don't re-read env variables on every request.
    """
    return Settings()

