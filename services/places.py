import logging
import aiohttp
from dataclasses import dataclass
from config import config

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

PLACE_TYPES = {
    "sto": {"type": "car_repair", "keyword": "автосервис СТО", "label": "🔧 СТО"},
    "tire": {"type": "car_repair", "keyword": "шиномонтаж", "label": "🛞 Шиномонтаж"},
    "parts": {"type": "car_dealer", "keyword": "автозапчасти", "label": "🔩 Запчасти"},
    "battery": {"type": "car_repair", "keyword": "аккумулятор замена", "label": "🔋 АКБ"},
    "gas": {"type": "gas_station", "keyword": "АЗС заправка", "label": "⛽ Заправка"},
}

def detect_category(problem: str) -> str:
    text = problem.lower()
    if any(w in text for w in ["шин", "колес", "прокол", "резин", "спустил"]):
        return "tire"
    if any(w in text for w in ["аккумулятор", "акб", "не заводит", "заряд"]):
        return "battery"
    if any(w in text for w in ["запчаст", "деталь", "купить"]):
        return "parts"
    if any(w in text for w in ["бензин", "топливо", "заправ"]):
        return "gas"
    return "sto"

import math

def _distance(lat1, lon1, lat2, lon2) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

async def _get_phone(session: aiohttp.ClientSession, place_id: str) -> str:
    params = {
        "place_id": place_id,
        "fields": "formatted_phone_number",
        "language": "ru",
        "key": config.GOOGLE_PLACES_API_KEY,
    }
    try:
        async with session.get(
            DETAILS_URL,
            params=params,
            timeout=aiohttp.ClientTimeout(total=5)
        ) as resp:
            data = await resp.json()
            return data.get("result", {}).get("formatted_phone_number", "Нет данных")
    except Exception:
        return "Нет данных"

async def search_places(lat: float, lon: float, category: str) -> list[Place]:
    cat = PLACE_TYPES.get(category, PLACE_TYPES["sto"])
    params = {
        "location": f"{lat},{lon}",
        "radius": config.SEARCH_RADIUS,
        "type": cat["type"],
        "keyword": cat["keyword"],
        "language": "ru",
        "key": config.GOOGLE_PLACES_API_KEY,
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                PLACES_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                data = await resp.json()
        except Exception as e:
            logger.error(f"Places ошибка: {e}")
            return []

        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            logger.error(f"Places статус: {data.get('status')}")
            return []

        all_places = []
        for place in data.get("results", []):
            rating = place.get("rating", 0)
            if rating < config.MIN_RATING:
                continue

            place_id = place.get("place_id", "")
            phone = await _get_phone(session, place_id)

            place_lat = place["geometry"]["location"]["lat"]
            place_lon = place["geometry"]["location"]["lng"]
            dist = _distance(lat, lon, place_lat, place_lon)

            # 2GIS маршрут
            route_url = f"https://2gis.ru/routeSearch/rsType/car/to/{place_lon},{place_lat}"
            maps_url = f"https://2gis.ru/search/{place.get('name', '')}"

            all_places.append(Place(
                name=place.get("name", "Без названия"),
                address=place.get("vicinity", "Адрес неизвестен"),
                rating=rating,
                phone=phone,
                maps_url=maps_url,
                route_url=route_url,
                place_type=cat["label"],
                distance=dist,
            ))

        # 2 лучших по рейтингу
        by_rating = sorted(all_places, key=lambda p: p.rating, reverse=True)[:2]

        # 3 ближайших
        by_distance = sorted(all_places, key=lambda p: p.distance)[:3]

        # Объединяем без дублей
        seen = set()
        result = []
        for place in by_rating + by_distance:
            if place.name not in seen:
                seen.add(place.name)
                result.append(place)

        return result[:5]

def format_places_message(places: list[Place], category: str, location_name: str = "") -> str:
    if not places:
        return "К сожалению, подходящих сервисов рядом не нашлось. Попробуйте другой адрес."

    cat = PLACE_TYPES.get(category, PLACE_TYPES["sto"])
    lines = [f"Нашёл {cat['label']} рядом с {location_name}:\n"]

    for i, place in enumerate(places, 1):
        dist_text = f"{place.distance:.1f} км"
        lines.append(
            f"{i}. *{place.name}*\n"
            f"   ⭐ {place.rating} | 📏 {dist_text}\n"
            f"   📍 {place.address}\n"
            f"   📞 {place.phone}\n"
            f"   [Открыть в 2ГИС]({place.maps_url})\n"
            f"   [Проложить маршрут]({place.route_url})\n"
        )

    lines.append("_Рейтинг 4.0+ | Маршруты через 2ГИС_ 🗺")
    return "\n".join(lines)

