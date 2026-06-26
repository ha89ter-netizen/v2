import asyncio
import os
import sys

import aiohttp
from dotenv import load_dotenv
from openai import AsyncOpenAI


load_dotenv()


def _print_status(name: str, ok: bool, detail: str = ""):
    status = "OK" if ok else "FAIL"
    suffix = f" ({detail})" if detail else ""
    print(f"{name} {status}{suffix}")


def _require_env(name: str) -> str:
    value = os.getenv(name, "")
    _print_status(name, bool(value))
    return value


async def _check_telegram(token: str) -> bool:
    if not token:
        return False

    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                ok = bool(data.get("ok"))
                _print_status("Telegram getMe", ok)
                return ok
    except Exception as exc:
        _print_status("Telegram getMe", False, exc.__class__.__name__)
        return False


async def _check_openai(api_key: str) -> bool:
    if not api_key:
        return False

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = AsyncOpenAI(api_key=api_key)
    try:
        response = await client.chat.completions.create(
            model=model,
            max_tokens=5,
            messages=[
                {"role": "system", "content": "Reply with OK only."},
                {"role": "user", "content": "health check"},
            ],
        )
        ok = bool(response.choices and response.choices[0].message.content)
        _print_status("OpenAI", ok)
        return ok
    except Exception as exc:
        _print_status("OpenAI", False, exc.__class__.__name__)
        return False


async def _check_google_geocode(api_key: str) -> bool:
    if not api_key:
        return False

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": "New York, NY",
        "key": api_key,
        "language": "ru",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                ok = data.get("status") == "OK" and bool(data.get("results"))
                _print_status("Google Geocode", ok, "" if ok else data.get("status", "unknown"))
                return ok
    except Exception as exc:
        _print_status("Google Geocode", False, exc.__class__.__name__)
        return False


async def _check_google_places(api_key: str) -> bool:
    if not api_key:
        return False

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": "40.7128,-74.0060",
        "radius": 1500,
        "type": "car_repair",
        "keyword": "auto repair",
        "key": api_key,
        "language": "ru",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                status = data.get("status")
                ok = status in ("OK", "ZERO_RESULTS")
                _print_status("Google Places", ok, "" if ok else status or "unknown")
                return ok
    except Exception as exc:
        _print_status("Google Places", False, exc.__class__.__name__)
        return False


async def main() -> int:
    telegram_token = _require_env("TELEGRAM_TOKEN")
    openai_key = _require_env("OPENAI_API_KEY")
    google_key = _require_env("GOOGLE_PLACES_API_KEY")

    checks = await asyncio.gather(
        _check_telegram(telegram_token),
        _check_openai(openai_key),
        _check_google_geocode(google_key),
        _check_google_places(google_key),
    )
    return 0 if all(checks) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
