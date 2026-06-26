import unittest

from tests._env import setup_test_env

setup_test_env()

from services.parts.budget_filter import choose_recommendation, parse_budget
from services.parts.oem_lookup import PartOption, lookup_parts
from services.parts.parts_classifier import PARTS, classify_part_request, format_candidates, infer_part_candidates, should_offer_parts
from services.parts.parts_response_builder import build_parts_response
from services.parts.search_query_builder import build_search_links
from services.parts.vin_parts_service import SUPPORTED_VEHICLES, VehicleContext, vehicle_catalog_key, vehicle_from_text


class PartsTests(unittest.IsolatedAsyncioTestCase):
    def test_vehicle_catalog_keys(self):
        cases = {
            "Toyota Sequoia 2018": "toyota_sequoia_2018",
            "Toyota Camry 70": "toyota_camry_70",
            "Hyundai Elantra 2020": "hyundai_elantra",
            "Kia Sportage 2021": "kia_sportage",
            "BMW G30 530i": "bmw_g30",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(vehicle_catalog_key(vehicle_from_text(text)), expected)

    def test_supported_vehicle_catalog_has_cis_market_coverage(self):
        self.assertEqual(len(SUPPORTED_VEHICLES), 100)
        for key, meta in SUPPORTED_VEHICLES.items():
            with self.subTest(vehicle=meta["display"]):
                self.assertEqual(vehicle_catalog_key(vehicle_from_text(meta["display"])), key)

    def test_vehicle_from_text_keeps_plain_vin(self):
        vehicle = vehicle_from_text("JTDBR32E720012345")

        self.assertEqual(vehicle.vin, "JTDBR32E720012345")
        self.assertEqual(vehicle.display_name, "VIN: JTDBR32E720012345")

    def test_vehicle_from_text_removes_embedded_vin_from_display_name(self):
        vehicle = vehicle_from_text("Toyota Camry 2019 (VIN: JTDBR32E720012345)")

        self.assertEqual(vehicle.vin, "JTDBR32E720012345")
        self.assertEqual(vehicle.make, "Toyota")
        self.assertEqual(vehicle.model, "Camry")
        self.assertEqual(vehicle.year, "2019")

    def test_classifier_detects_likely_replacement_part(self):
        candidates = infer_part_candidates("Машину трясет на холостых, троит")
        self.assertEqual(candidates[0].part.key, "ignition_coil")
        self.assertGreaterEqual(candidates[0].confidence, 60)
        self.assertTrue(should_offer_parts(candidates))

    def test_classifier_detects_english_likely_replacement_part(self):
        candidates = infer_part_candidates("Engine shakes on rough idle and has misfire")
        self.assertEqual(candidates[0].part.key, "ignition_coil")
        self.assertGreaterEqual(candidates[0].confidence, 60)
        self.assertIn("Likely parts", format_candidates(candidates, language_code="en"))

    def test_direct_part_classification(self):
        candidate = classify_part_request("тормозные колодки")
        self.assertEqual(candidate.part.key, "brake_pads")
        self.assertEqual(candidate.part.system, "brake")

    async def test_mock_catalog_returns_three_options_for_supported_cars(self):
        vehicles = [
            VehicleContext("Toyota", "Sequoia", "2018", display_name="Toyota Sequoia 2018"),
            VehicleContext("Toyota", "Camry 70", "", display_name="Toyota Camry 70"),
            VehicleContext("Hyundai", "Elantra", "2020", display_name="Hyundai Elantra"),
            VehicleContext("Kia", "Sportage", "2021", display_name="Kia Sportage"),
            VehicleContext("BMW", "G30", "2019", display_name="BMW G30"),
        ]
        for vehicle in vehicles:
            with self.subTest(vehicle=vehicle.display_name):
                options = await lookup_parts(vehicle, "ignition_coil")
                self.assertEqual(len(options), 3)
                self.assertEqual({option.classification for option in options}, {
                    "original_oem",
                    "trusted_aftermarket",
                    "cheap_aftermarket",
                })

    async def test_mock_catalog_uses_vehicle_specific_prefixes_for_all_supported_cars(self):
        for meta in SUPPORTED_VEHICLES.values():
            vehicle = vehicle_from_text(meta["display"])
            with self.subTest(vehicle=meta["display"]):
                options = await lookup_parts(vehicle, "brake_pads")
                self.assertEqual(len(options), 3)
                self.assertTrue(options[0].part_number.startswith(meta["prefix"]))
                self.assertNotIn("GEN-", options[0].part_number)

    async def test_budget_prefers_trusted_when_original_is_too_expensive(self):
        vehicle = VehicleContext("Toyota", "Sequoia", "2018", display_name="Toyota Sequoia 2018")
        options = await lookup_parts(vehicle, "ignition_coil")
        recommendation = choose_recommendation(options, PARTS["ignition_coil"], parse_budget("до 50 000 ₸"))
        self.assertEqual(recommendation.recommended.classification, "trusted_aftermarket")
        self.assertIn("Оригинал выше бюджета", recommendation.budget_note)

    def test_unknown_not_primary_for_safety_system(self):
        unknown = PartOption("brake_pads", "тормозные колодки", "brake pads", "???", "X", "unknown", 1000)
        recommendation = choose_recommendation([unknown], PARTS["brake_pads"], parse_budget("до 20 000 ₸"))
        self.assertEqual(recommendation.recommended.classification, "unknown")
        self.assertIn("Нельзя рекомендовать unknown", recommendation.warning)

    async def test_response_contains_search_links(self):
        vehicle = VehicleContext("Toyota", "Sequoia", "2018", display_name="Toyota Sequoia 2018")
        options = await lookup_parts(vehicle, "ignition_coil")
        recommendation = choose_recommendation(options, PARTS["ignition_coil"], None)
        response = build_parts_response(vehicle, recommendation)
        self.assertIn("OEM оригинал", response)
        self.assertIn("Номер:", response)
        self.assertIn("3. Где искать", response)
        self.assertIn("[OEM оригинал](", response)
        self.assertIn("google.com/search", response)
        self.assertIn("Перед покупкой сверяйте", response)
        self.assertNotIn("OEM поиск: https://", response)

    async def test_english_response_contains_clear_search_links(self):
        vehicle = VehicleContext("Toyota", "Sequoia", "2018", display_name="Toyota Sequoia 2018")
        options = await lookup_parts(vehicle, "ignition_coil")
        recommendation = choose_recommendation(options, PARTS["ignition_coil"], None)
        response = build_parts_response(vehicle, recommendation, "en")
        self.assertIn("Parts match for Toyota Sequoia 2018", response)
        self.assertIn("OEM original", response)
        self.assertIn("Part number:", response)
        self.assertIn("[OEM original search](", response)
        self.assertIn("Before buying", response)

    async def test_search_query_builder_uses_vehicle_and_part(self):
        vehicle = VehicleContext("Toyota", "Sequoia", "2018", display_name="Toyota Sequoia 2018")
        option = (await lookup_parts(vehicle, "ignition_coil"))[0]
        links = build_search_links(vehicle, option)
        self.assertEqual(len(links), 4)
        self.assertIn("Toyota Sequoia 2018 ignition coil", links[0].query)


if __name__ == "__main__":
    unittest.main()
