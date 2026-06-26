import tempfile
import unittest
from pathlib import Path

from tests._env import setup_test_env

setup_test_env()

import database
from config import config
from handlers import location


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
    payload = {}
    last_params = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def get(self, url, params=None, timeout=None):
        type(self).last_params = params
        return _FakeResponse(type(self).payload)


class LocationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        database.DB_PATH = str(Path(self.tmpdir.name) / "test.sqlite3")
        await database.init_db()
        self.original_session = location.aiohttp.ClientSession
        self.original_country = config.DEFAULT_COUNTRY
        self.original_country_code = config.DEFAULT_COUNTRY_CODE
        location.aiohttp.ClientSession = _FakeSession
        _FakeSession.last_params = None
        config.DEFAULT_COUNTRY = "Kazakhstan"
        config.DEFAULT_COUNTRY_CODE = "KZ"

    async def asyncTearDown(self):
        location.aiohttp.ClientSession = self.original_session
        config.DEFAULT_COUNTRY = self.original_country
        config.DEFAULT_COUNTRY_CODE = self.original_country_code
        self.tmpdir.cleanup()

    def test_manual_address_query_adds_city_and_country(self):
        self.assertEqual(
            location.build_manual_address_query("Алматы", "Абая 10"),
            "Абая 10, Алматы, Kazakhstan",
        )

    async def test_geocode_uses_country_component(self):
        _FakeSession.payload = {
            "status": "OK",
            "results": [
                {
                    "formatted_address": "проспект Абая 10, Алматы, Казахстан",
                    "geometry": {"location": {"lat": 43.2389, "lng": 76.8897}},
                    "address_components": [
                        {"short_name": "KZ", "types": ["country", "political"]},
                    ],
                }
            ],
        }

        lat, lon, formatted = await location.geocode_address("Абая 10, Алматы, Kazakhstan")

        self.assertEqual((lat, lon, formatted), (43.2389, 76.8897, "проспект Абая 10, Алматы, Казахстан"))
        self.assertEqual(_FakeSession.last_params["components"], "country:KZ")
        self.assertEqual(_FakeSession.last_params["region"], "kz")

    async def test_geocode_rejects_wrong_country_result(self):
        _FakeSession.payload = {
            "status": "OK",
            "results": [
                {
                    "formatted_address": "улица Абая 10, Москва, Россия",
                    "geometry": {"location": {"lat": 55.7558, "lng": 37.6173}},
                    "address_components": [
                        {"short_name": "RU", "types": ["country", "political"]},
                    ],
                }
            ],
        }

        lat, lon, formatted = await location.geocode_address("Абая 10, Алматы, Kazakhstan")

        self.assertIsNone(lat)
        self.assertIsNone(lon)
        self.assertEqual(formatted, "Абая 10, Алматы, Kazakhstan")


if __name__ == "__main__":
    unittest.main()
