import logging
import aiohttp
from urllib.parse import quote
from dataclasses import dataclass
from typing import Optional
from config import config
from database import record_api_usage
from services.retry import retry_async
from services.service_categories import SERVICE_CATEGORIES
from services.i18n import is_english
from utils import escape_markdown, normalize_text_key

logger = logging.getLogger(__name__)

PLACES_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

@dataclass
class Place:
    name: str
    address: str
    rating: float
    phone: str
    maps_url: str
    route_url: str
    place_type: str
    distance: float = 0.0

PLACE_TYPES = SERVICE_CATEGORIES

def _has_category_words(text: str, keywords: list[str]) -> bool:
    words = text.split()
    for keyword in keywords:
        key = normalize_text_key(keyword)
        if not key:
            continue
        if " " in key and key in text:
            return True
        if any(word == key or word.startswith(key) for word in words):
            return True
    return False

def detect_category(problem: str) -> str:
    text = normalize_text_key(problem)
    if _has_category_words(text, ["дилер", "дилерский центр", "официальный дилер", "официальный сервис", "гарантия", "гарантийный", "dealer", "dealer center", "official dealer", "authorized dealer", "authorized service", "warranty"]):
        return "dealer"
    if _has_category_words(text, ["сход развал", "развал", "схождение", "тянет руль", "руль криво", "wheel alignment", "alignment", "pulls to side", "steering wheel crooked"]):
        return "alignment"
    if _has_category_words(text, ["шина", "шины", "шиномонтаж", "колесо", "колеса", "прокол", "резина", "спустило", "tire", "tyre", "tire shop", "puncture", "flat tire", "wheel"]):
        return "tire"
    if _has_category_words(text, ["диагностика", "диагност", "ошибка", "сканер", "diagnostics", "diagnostic", "scanner", "error code"]):
        return "diagnostics"
    if _has_category_words(text, ["электрик", "автоэлектрик", "проводка", "генератор", "стартер", "электрика", "electrician", "auto electrician", "wiring", "alternator", "starter", "electrical"]):
        return "electric"
    if _has_category_words(text, ["кузов", "кузовной", "малярка", "покраска", "бампер", "вмятина", "body repair", "paint", "bumper", "dent"]):
        return "body"
    if _has_category_words(text, ["стекл", "стекло", "лобовое", "автостекло", "трещина стекла", "auto glass", "windshield", "glass crack"]):
        return "glass"
    if _has_category_words(text, ["кондиционер", "кондей", "не холодит", "фреон", "air conditioning", "a/c", "ac service", "freon", "not cold"]):
        return "ac"
    if _has_category_words(text, ["авторазбор", "разбор", "б у", "бу запчасти", "контрактная деталь", "salvage yard", "used parts", "used auto parts"]):
        return "salvage"
    if _has_category_words(text, ["аккумулятор", "акб", "не заводит", "заряд", "battery", "car battery", "dead battery"]):
        return "battery"
    if _has_category_words(text, ["запчасти", "запчасть", "деталь", "купить", "parts", "part", "parts store", "buy part"]):
        return "parts"
    if _has_category_words(text, ["бензин", "топливо", "заправка", "заправить", "gas", "fuel", "gas station", "refuel"]):
        return "gas"
    if _has_category_words(text, ["мойка", "помыть", "автомойка", "car wash", "wash"]):
        return "wash"
    if _has_category_words(text, ["детейлинг", "полировка", "химчистка", "detailing", "polishing", "interior cleaning"]):
        return "detailing"
    if _has_category_words(text, ["замена масла", "масло поменять", "oil change", "change oil"]):
        return "oil"
    if _has_category_words(text, ["эвакуатор", "срочно", "помощь на дороге", "не могу ехать", "tow truck", "roadside assistance", "urgent", "cannot drive"]):
        return "tow"
    return "sto"

import math

def _distance(lat1, lon1, lat2, lon2) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def _place_location(place: dict) -> Optional[tuple[float, float]]:
    location = place.get("geometry", {}).get("location", {})
    place_lat = location.get("lat")
    place_lon = location.get("lng")
    if place_lat is None or place_lon is None:
        return None
    return float(place_lat), float(place_lon)

async def _get_details(session: aiohttp.ClientSession, place_id: str) -> tuple[str, str]:
    if not place_id:
        return "Нет данных", ""

    params = {
        "place_id": place_id,
        "fields": "formatted_phone_number,formatted_address",
        "language": "ru",
        "key": config.GOOGLE_PLACES_API_KEY,
    }
    attempts = 1
    try:
        async def action():
            async with session.get(
                DETAILS_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                return await resp.json()

        data, attempts = await retry_async(action, config.GOOGLE_MAX_RETRIES)
        ok = data.get("status") in ("OK", "ZERO_RESULTS")
        await record_api_usage(
            provider="google",
            operation="place_details",
            success=ok,
            attempts=attempts,
            estimated_cost_usd=config.GOOGLE_PLACES_COST_PER_REQUEST,
            error="" if ok else data.get("status", "unknown"),
        )
        result = data.get("result", {})
        return (
            result.get("formatted_phone_number", "Нет данных"),
            result.get("formatted_address", ""),
        )
    except Exception as e:
        await record_api_usage(
            provider="google",
            operation="place_details",
            success=False,
            attempts=attempts,
            estimated_cost_usd=config.GOOGLE_PLACES_COST_PER_REQUEST,
            error=str(e),
        )
        return "Нет данных", ""

async def search_places(
    lat: float,
    lon: float,
    category: str,
    radius: Optional[int] = None,
    min_rating: Optional[float] = None,
    limit: int = 5,
) -> list[Place]:
    cat = PLACE_TYPES.get(category, PLACE_TYPES["sto"])
    keywords = cat.get("keywords", [cat.get("keyword", "")])
    radius = radius or cat.get("radius", config.SEARCH_RADIUS)
    min_rating = cat.get("min_rating", config.MIN_RATING) if min_rating is None else min_rating

    async with aiohttp.ClientSession() as session:
        raw_results = {}
        all_places = []

        for keyword in keywords:
            params = {
                "location": f"{lat},{lon}",
                "radius": radius,
                "keyword": keyword,
                "language": "ru",
                "key": config.GOOGLE_PLACES_API_KEY,
            }
            if cat.get("type"):
                params["type"] = cat["type"]

            attempts = 1
            try:
                async def action():
                    async with session.get(
                        PLACES_URL,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as resp:
                        return await resp.json()

                data, attempts = await retry_async(action, config.GOOGLE_MAX_RETRIES)
            except Exception as e:
                logger.error(f"Places ошибка: {e}")
                await record_api_usage(
                    provider="google",
                    operation="nearby_search",
                    success=False,
                    attempts=attempts,
                    estimated_cost_usd=config.GOOGLE_PLACES_COST_PER_REQUEST,
                    error=str(e),
                )
                continue

            if data.get("status") not in ("OK", "ZERO_RESULTS"):
                logger.error(f"Places статус: {data.get('status')}")
                await record_api_usage(
                    provider="google",
                    operation="nearby_search",
                    success=False,
                    attempts=attempts,
                    estimated_cost_usd=config.GOOGLE_PLACES_COST_PER_REQUEST,
                    error=data.get("status", "unknown"),
                )
                continue

            await record_api_usage(
                provider="google",
                operation="nearby_search",
                success=True,
                attempts=attempts,
                estimated_cost_usd=config.GOOGLE_PLACES_COST_PER_REQUEST,
            )

            for place in data.get("results", []):
                key = place.get("place_id") or f"{place.get('name', '')}:{place.get('vicinity', '')}"
                raw_results[key] = place

        max_distance_km = radius / 1000

        for place in raw_results.values():
            rating = place.get("rating", 0) or 0
            if rating < min_rating:
                continue

            location = _place_location(place)
            if not location:
                continue
            place_lat, place_lon = location
            dist = _distance(lat, lon, place_lat, place_lon)
            if dist > max_distance_km:
                continue

            place_id = place.get("place_id", "")
            phone, formatted_address = await _get_details(session, place_id)

            route_url = f"https://www.google.com/maps/dir/?api=1&destination={place_lat},{place_lon}&travelmode=driving"
            maps_url = f"https://www.google.com/maps/search/?api=1&query={place_lat},{place_lon}"
            if place_id:
                route_url += f"&destination_place_id={quote(place_id)}"
                maps_url += f"&query_place_id={quote(place_id)}"

            all_places.append(Place(
                name=place.get("name", "Без названия"),
                address=formatted_address or place.get("vicinity", "Адрес неизвестен"),
                rating=rating,
                phone=phone,
                maps_url=maps_url,
                route_url=route_url,
                place_type=cat["label"],
                distance=dist,
            ))

        if not all_places and min_rating:
            for place in raw_results.values():
                location = _place_location(place)
                if not location:
                    continue
                place_lat, place_lon = location
                dist = _distance(lat, lon, place_lat, place_lon)
                if dist > max_distance_km:
                    continue
                place_id = place.get("place_id", "")
                phone, formatted_address = await _get_details(session, place_id)
                route_url = f"https://www.google.com/maps/dir/?api=1&destination={place_lat},{place_lon}&travelmode=driving"
                maps_url = f"https://www.google.com/maps/search/?api=1&query={place_lat},{place_lon}"
                if place_id:
                    route_url += f"&destination_place_id={quote(place_id)}"
                    maps_url += f"&query_place_id={quote(place_id)}"
                all_places.append(Place(
                    name=place.get("name", "Без названия"),
                    address=formatted_address or place.get("vicinity", "Адрес неизвестен"),
                    rating=place.get("rating", 0) or 0,
                    phone=phone,
                    maps_url=maps_url,
                    route_url=route_url,
                    place_type=cat["label"],
                    distance=dist,
                ))

        # 3 лучших по рейтингу

        by_rating = sorted(all_places, key=lambda p: p.rating, reverse=True)[:3]

        # 3 ближайших
        by_distance = sorted(all_places, key=lambda p: p.distance)[:3]

        # Объединяем без дублей
        seen = set()
        result = []
        for place in by_rating + by_distance:
            if place.name not in seen:
                seen.add(place.name)
                result.append(place)

        return result[:limit]

def format_places_message(places: list[Place], category: str, location_name: str = "", language_code: str = "") -> str:
    english = is_english(language_code)
    if not places:
        if english:
            return (
                "I could not find suitable places nearby.\n\n"
                "You can increase the radius, lower the rating filter, choose another category, "
                "or enter another address."
            )
        return "К сожалению, подходящих сервисов рядом не нашлось.\n\nМожно увеличить радиус, снизить минимальный рейтинг, выбрать другую категорию или ввести другой адрес."

    cat = PLACE_TYPES.get(category, PLACE_TYPES["sto"])
    label = cat.get("label_en") if english else cat["label"]
    if english:
        lines = [f"Found {label} near {escape_markdown(location_name)}:\n"]
    else:
        lines = [f"Нашёл {label} рядом с {escape_markdown(location_name)}:\n"]

    for i, place in enumerate(places, 1):
        dist_text = f"{place.distance:.1f} км"
        map_label = "Open on map" if english else "Открыть на карте"
        route_label = "Build route" if english else "Проложить маршрут"
        lines.append(
            f"{i}. *{escape_markdown(place.name)}*\n"
            f"   ⭐ {escape_markdown(place.rating)} | 📏 {escape_markdown(dist_text)}\n"
            f"   📍 {escape_markdown(place.address)}\n"
            f"   📞 {escape_markdown(place.phone)}\n"
            f"   [{map_label}]({place.maps_url})\n"
            f"   [{route_label}]({place.route_url})\n"
        )

    if category == "tow":
        lines.append("_Searching within up to 12 km. For urgent cases, call several places and do not continue driving if it is unsafe._" if english else "_Ищу в радиусе до 12 км. Для срочных случаев звоните в несколько мест подряд и не продолжайте движение, если это опасно._")
    else:
        lines.append("_Searching near your location. I show rating 4.0+ first; if there are none, I show the nearest found places._ 🗺" if english else "_Ищу рядом с вашей геолокацией. Сначала показываю рейтинг 4.0+, если таких нет — ближайшие найденные места._ 🗺")
    return "\n".join(lines)
