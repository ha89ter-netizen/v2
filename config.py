import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    TELEGRAM_TOKEN: str
    OPENAI_API_KEY: str
    GOOGLE_PLACES_API_KEY: str
    MIN_RATING: float = 4.0
    SEARCH_RADIUS: int = 5000

def _load_config() -> Config:
    token = os.getenv("TELEGRAM_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")
    google_key = os.getenv("GOOGLE_PLACES_API_KEY")

    missing = []
    if not token: missing.append("TELEGRAM_TOKEN")
    if not openai_key: missing.append("OPENAI_API_KEY")
    if not google_key: missing.append("GOOGLE_PLACES_API_KEY")

    if missing:
        raise EnvironmentError(f"Не заданы ключи: {', '.join(missing)}")

    return Config(
        TELEGRAM_TOKEN=token,
        OPENAI_API_KEY=openai_key,
        GOOGLE_PLACES_API_KEY=google_key,
    )

config = _load_config()

