import unittest

from tests._env import setup_test_env

setup_test_env()

from services import vin_decoder
from services.vin_decoder import clean_vin, decode_vin


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
    last_url = ""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def get(self, url, timeout=None):
        type(self).last_url = url
        return _FakeResponse({
            "Results": [
                {"Variable": "Make", "Value": "TOYOTA"},
                {"Variable": "Model", "Value": "CAMRY"},
                {"Variable": "Model Year", "Value": "2019"},
            ]
        })


class VinDecoderTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.original_session = vin_decoder.aiohttp.ClientSession
        vin_decoder.aiohttp.ClientSession = _FakeSession
        _FakeSession.last_url = ""

    async def asyncTearDown(self):
        vin_decoder.aiohttp.ClientSession = self.original_session

    def test_clean_vin_accepts_spaces_and_hyphens(self):
        self.assertEqual(clean_vin("jtd-br32e-720012345"), "JTDBR32E720012345")

    def test_clean_vin_rejects_invalid_symbols(self):
        self.assertEqual(clean_vin("JTDBR32E72001234O"), "")

    async def test_decode_vin_returns_vehicle_info(self):
        info = await decode_vin("jtd-br32e-720012345")

        self.assertEqual(info["manufacturer"], "TOYOTA")
        self.assertEqual(info["model"], "CAMRY")
        self.assertEqual(info["year"], "2019")
        self.assertEqual(info["vin"], "JTDBR32E720012345")
        self.assertIn("JTDBR32E720012345", _FakeSession.last_url)


if __name__ == "__main__":
    unittest.main()
