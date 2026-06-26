import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    TELEGRAM_TOKEN: str
    OPENAI_API_KEY: str
    GOOGLE_PLACES_API_KEY: str
    ADMIN_IDS: set[int]
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_VISION_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_RETRIES: int = 2
    GOOGLE_MAX_RETRIES: int = 2
    OPENAI_INPUT_COST_PER_1M: float = 0.0
    OPENAI_OUTPUT_COST_PER_1M: float = 0.0
    GOOGLE_PLACES_COST_PER_REQUEST: float = 0.0
    GOOGLE_GEOCODE_COST_PER_REQUEST: float = 0.0
    REMINDER_CHECK_INTERVAL_SECONDS: int = 3600
    MIN_RATING: float = 4.0
    SEARCH_RADIUS: int = 5000
    DEFAULT_COUNTRY: str = "Kazakhstan"
    DEFAULT_COUNTRY_CODE: str = "KZ"

def _get_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        raise EnvironmentError(f"{name} должен быть числом")

def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        raise EnvironmentError(f"{name} должен быть целым числом")

def _get_admin_ids() -> set[int]:
    raw = os.getenv("ADMIN_IDS", "")
    if not raw.strip():
        return set()
    try:
        return {int(item.strip()) for item in raw.split(",") if item.strip()}
    except ValueError:
        raise EnvironmentError("ADMIN_IDS должен быть списком чисел через запятую")

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
        ADMIN_IDS=_get_admin_ids(),
        OPENAI_MODEL=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        OPENAI_VISION_MODEL=os.getenv("OPENAI_VISION_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini")),
        OPENAI_MAX_RETRIES=_get_int("OPENAI_MAX_RETRIES", 2),
        GOOGLE_MAX_RETRIES=_get_int("GOOGLE_MAX_RETRIES", 2),
        OPENAI_INPUT_COST_PER_1M=_get_float("OPENAI_INPUT_COST_PER_1M", 0.0),
        OPENAI_OUTPUT_COST_PER_1M=_get_float("OPENAI_OUTPUT_COST_PER_1M", 0.0),
        GOOGLE_PLACES_COST_PER_REQUEST=_get_float("GOOGLE_PLACES_COST_PER_REQUEST", 0.0),
        GOOGLE_GEOCODE_COST_PER_REQUEST=_get_float("GOOGLE_GEOCODE_COST_PER_REQUEST", 0.0),
        REMINDER_CHECK_INTERVAL_SECONDS=_get_int("REMINDER_CHECK_INTERVAL_SECONDS", 3600),
        MIN_RATING=_get_float("MIN_RATING", 4.0),
        SEARCH_RADIUS=_get_int("SEARCH_RADIUS", 5000),
        DEFAULT_COUNTRY=os.getenv("DEFAULT_COUNTRY", "Kazakhstan"),
        DEFAULT_COUNTRY_CODE=os.getenv("DEFAULT_COUNTRY_CODE", "KZ").upper(),
    )

config = _load_config()
