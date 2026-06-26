import os


def setup_test_env() -> None:
    os.environ.setdefault("TELEGRAM_TOKEN", "test-telegram-token")
    os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
    os.environ.setdefault("GOOGLE_PLACES_API_KEY", "test-google-key")
    os.environ.setdefault("OPENAI_MODEL", "gpt-4o-mini")
    os.environ.setdefault("OPENAI_VISION_MODEL", "gpt-4o-mini")
    os.environ.setdefault("OPENAI_MAX_RETRIES", "0")
    os.environ.setdefault("GOOGLE_MAX_RETRIES", "0")

