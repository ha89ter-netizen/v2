import unittest

from tests._env import setup_test_env

setup_test_env()

from services.intent import detect_local_intent
from services.safety import detect_safety_risk


class IntentSafetyTests(unittest.TestCase):
    def test_service_requests_are_not_treated_as_diagnosis(self):
        cases = {
            "найди шиномонтаж рядом": "find_service",
            "где ближайшая заправка": "find_service",
            "нужен эвакуатор": "find_service",
            "хочу автомойку рядом": "find_service",
            "где заменить масло рядом": "find_service",
            "где помыть машину": "find_service",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(detect_local_intent(text), expected)

    def test_diy_question_stays_diy(self):
        self.assertEqual(detect_local_intent("как заменить масло самому"), "diy_repair")

    def test_problem_text_is_diagnosis(self):
        cases = [
            "горит чек и машина троит",
            "руль скрипит при повороте",
            "аккумулятор сел не заводится",
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(detect_local_intent(text), "diagnose")

    def test_steering_word_alone_is_not_critical(self):
        result = detect_safety_risk("руль скрипит при повороте")
        self.assertEqual(result["risk_level"], "normal")

    def test_critical_steering_and_brakes_are_detected(self):
        cases = [
            "руль заклинило на дороге",
            "тормоза отказали педаль провалилась",
            "течет бензин и запах бензина",
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(detect_safety_risk(text)["risk_level"], "critical")


if __name__ == "__main__":
    unittest.main()
