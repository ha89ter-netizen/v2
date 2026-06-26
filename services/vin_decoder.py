from typing import Optional

import aiohttp


def clean_vin(text: str) -> str:
    value = (text or "").strip().upper().replace(" ", "").replace("-", "")
    if len(value) == 17 and value.isalnum() and not any(char in value for char in "IOQ"):
        return value
    return ""


async def decode_vin(vin: str) -> Optional[dict]:
    clean = clean_vin(vin)
    if not clean:
        return None

    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{clean}?format=json"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                data = await resp.json()
                results = data.get("Results", [])

                info = {}
                for item in results:
                    if item["Variable"] == "Make":
                        info["manufacturer"] = item["Value"] or "Неизвестно"
                    if item["Variable"] == "Model":
                        info["model"] = item["Value"] or ""
                    if item["Variable"] == "Model Year":
                        info["year"] = item["Value"] or "Неизвестен"

                if info.get("manufacturer"):
                    info["vin"] = clean
                    return info
        except Exception:
            return None
    return None
