import tempfile
import unittest
from pathlib import Path

from tests._env import setup_test_env

setup_test_env()

import database
from services import places
from services.places import Place, detect_category, format_places_message, search_places


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self):
        return self.payload


class _FakeSession:
    nearby_calls = 0
    detail_calls = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def get(self, url, params=None, timeout=None):
        if url == places.PLACES_URL:
            type(self).nearby_calls += 1
            return _FakeResponse({
                "status": "OK",
                "results": [
                    {
                        "place_id": "near-1",
                        "name": "Алматы Шиномонтаж",
                        "rating": 4.7,
                        "vicinity": "Абая 10",
                        "geometry": {"location": {"lat": 43.2385, "lng": 76.9455}},
                    },
                    {
                        "place_id": "near-2",
                        "name": "Колесо Сервис",
                        "rating": 4.2,
                        "vicinity": "Сейфуллина 20",
                        "geometry": {"location": {"lat": 43.2410, "lng": 76.9500}},
                    },
                    {
                        "place_id": "near-3",
                        "name": "Tire Help",
                        "rating": 4.9,
                        "vicinity": "Райымбека 30",
                        "geometry": {"location": {"lat": 43.2300, "lng": 76.9400}},
                    },
                    {
                        "place_id": "far-ru",
                        "name": "Далёкий сервис",
                        "rating": 5.0,
                        "vicinity": "Москва",
                        "geometry": {"location": {"lat": 55.7558, "lng": 37.6173}},
                    },
                ],
            })

        type(self).detail_calls += 1
        place_id = params["place_id"]
        return _FakeResponse({
            "status": "OK",
            "result": {
                "formatted_phone_number": f"+7 {place_id}",
                "formatted_address": f"Адрес {place_id}",
            },
        })


class PlacesTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        database.DB_PATH = str(Path(self.tmpdir.name) / "test.sqlite3")
        await database.init_db()
        _FakeSession.nearby_calls = 0
        _FakeSession.detail_calls = 0
        self.original_session = places.aiohttp.ClientSession
        places.aiohttp.ClientSession = _FakeSession

    async def asyncTearDown(self):
        places.aiohttp.ClientSession = self.original_session
        self.tmpdir.cleanup()

    def test_detect_category(self):
        cases = {
            "пробило колесо и спустила шина": "tire",
            "нужен официальный дилерский центр по гарантии": "dealer",
            "нужна диагностика ошибки": "diagnostics",
            "нужен автоэлектрик проверить проводку": "electric",
            "после удара нужен кузовной ремонт": "body",
            "машину тянет руль нужен сход развал": "alignment",
            "трещина на лобовом стекле": "glass",
            "кондиционер не холодит": "ac",
            "ищу авторазбор и бу запчасти": "salvage",
            "где купить запчасти": "parts",
            "нужен эвакуатор срочно": "tow",
            "хочу помыть машину": "wash",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(detect_category(text), expected)

    def test_detect_category_english(self):
        cases = {
            "need an official dealer center for warranty": "dealer",
            "flat tire need nearest tire shop": "tire",
            "need diagnostics for check engine code": "diagnostics",
            "find auto electrician for wiring": "electric",
            "need body repair after accident": "body",
            "car pulls to side need wheel alignment": "alignment",
            "windshield glass crack": "glass",
            "ac service freon not cold": "ac",
            "used parts salvage yard": "salvage",
            "where to buy parts": "parts",
            "need tow truck urgent": "tow",
            "find car wash": "wash",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(detect_category(text), expected)

    def test_format_places_message_contains_routes(self):
        message = format_places_message(
            [
                Place(
                    name="СТО *Тест*",
                    address="Абая [10]",
                    rating=4.8,
                    phone="+7 777",
                    maps_url="https://www.google.com/maps/search/?api=1&query=43,76",
                    route_url="https://www.google.com/maps/dir/?api=1&destination=43,76",
                    place_type="🔧 СТО",
                    distance=1.2,
                )
            ],
            "sto",
            "Алматы",
        )
        self.assertIn("Открыть на карте", message)
        self.assertIn("Проложить маршрут", message)
        self.assertIn("СТО \\*Тест\\*", message)

    def test_format_places_message_english(self):
        message = format_places_message(
            [
                Place(
                    name="Test Repair",
                    address="Main 10",
                    rating=4.8,
                    phone="+1 777",
                    maps_url="https://www.google.com/maps/search/?api=1&query=43,76",
                    route_url="https://www.google.com/maps/dir/?api=1&destination=43,76",
                    place_type="🔧 Repair shop",
                    distance=1.2,
                )
            ],
            "sto",
            "Almaty",
            "en",
        )
        self.assertIn("Found 🔧 Repair shop near Almaty", message)
        self.assertIn("Open on map", message)
        self.assertIn("Build route", message)

    async def test_search_places_returns_multiple_nearby_and_filters_far_results(self):
        result = await search_places(43.2380, 76.9450, "tire")

        self.assertGreaterEqual(len(result), 3)
        self.assertTrue(all(place.distance <= 7 for place in result))
        self.assertNotIn("Далёкий сервис", {place.name for place in result})
        self.assertGreaterEqual(_FakeSession.nearby_calls, 1)
        self.assertEqual(_FakeSession.detail_calls, 3)


if __name__ == "__main__":
    unittest.main()
