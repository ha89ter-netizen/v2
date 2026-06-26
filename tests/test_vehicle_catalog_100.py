import unittest

from tests._env import setup_test_env

setup_test_env()

from services.parts.oem_lookup import lookup_parts
from services.parts.vin_parts_service import (
    SUPPORTED_VEHICLES,
    vehicle_catalog_key,
    vehicle_from_text,
)


class VehicleCatalogSizeTests(unittest.TestCase):
    def test_catalog_contains_exactly_100_supported_vehicles(self):
        self.assertEqual(len(SUPPORTED_VEHICLES), 100)

    def test_vehicle_keys_are_unique(self):
        self.assertEqual(len(SUPPORTED_VEHICLES), len(set(SUPPORTED_VEHICLES.keys())))

    def test_oem_prefixes_are_unique(self):
        prefixes = [meta["prefix"] for meta in SUPPORTED_VEHICLES.values()]
        self.assertEqual(len(prefixes), len(set(prefixes)))


def _make_vehicle_test(vehicle_key: str, meta: dict):
    async def test_vehicle(self):
        vehicle = vehicle_from_text(meta["display"])

        self.assertEqual(vehicle_catalog_key(vehicle), vehicle_key)

        options = await lookup_parts(vehicle, "brake_pads")
        self.assertEqual(len(options), 3)
        self.assertEqual(
            {option.classification for option in options},
            {"original_oem", "trusted_aftermarket", "cheap_aftermarket"},
        )
        self.assertTrue(options[0].part_number.startswith(meta["prefix"]))
        self.assertNotIn("GEN-", options[0].part_number)

    return test_vehicle


class EverySupportedVehiclePartsTests(unittest.IsolatedAsyncioTestCase):
    pass


for key, meta in SUPPORTED_VEHICLES.items():
    test_name = f"test_{key}_has_vehicle_specific_mock_parts"
    setattr(EverySupportedVehiclePartsTests, test_name, _make_vehicle_test(key, meta))


if __name__ == "__main__":
    unittest.main()
