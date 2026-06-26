import unittest

from tests._env import setup_test_env

setup_test_env()

from handlers.problem import ONSET_LABELS, _problem_with_onset
from services.deep_diagnostics import (
    detect_diagnostic_system,
    diagnostic_signal_score,
    diagnostic_questions_text,
    enrich_problem_context,
    needs_quick_clarification,
    quick_question_text,
)


class ProblemFlowTests(unittest.TestCase):
    def test_problem_with_onset_adds_context_for_ai(self):
        result = _problem_with_onset("Машину трясет на холостых", ONSET_LABELS["⚡ Внезапно"])

        self.assertIn("Машину трясет на холостых", result)
        self.assertIn("Вероятная система", result)
        self.assertIn("Динамика проблемы", result)
        self.assertIn("появилась внезапно", result)

    def test_problem_without_onset_keeps_original_text(self):
        self.assertEqual(_problem_with_onset("Скрипят тормоза", ""), "Скрипят тормоза")

    def test_deep_context_adds_user_details(self):
        result = _problem_with_onset(
            "Машину трясет на холостых",
            ONSET_LABELS["⚡ Внезапно"],
            details="на холодную сильнее, чек мигает",
        )

        self.assertIn("Уточнения пользователя", result)
        self.assertIn("чек мигает", result)

    def test_detects_engine_diagnostic_system(self):
        self.assertEqual(detect_diagnostic_system("машину трясет на холостых и троит"), "engine")

    def test_detects_brake_diagnostic_system(self):
        self.assertEqual(detect_diagnostic_system("скрипят тормоза и бьет педаль"), "brake")

    def test_diagnostic_questions_are_system_specific(self):
        text = diagnostic_questions_text("скрипят тормоза", "ru")

        self.assertIn("тормозная система", text)
        self.assertIn("Скрип", text)
        self.assertIn("Пропустить уточнение", text)

    def test_diagnostic_questions_are_english(self):
        text = diagnostic_questions_text("engine shakes at idle", "en")

        self.assertIn("engine / ignition / fuel", text)
        self.assertIn("rough idle", enrich_problem_context("engine shakes at rough idle", "", "", "en"))
        self.assertIn("Skip details", text)

    def test_short_vague_problem_needs_only_quick_clarification(self):
        self.assertTrue(needs_quick_clarification("машина странно едет"))
        text = quick_question_text("машина странно едет", "ru")

        self.assertIn("один короткий вопрос", text)
        self.assertIn("Пропустить уточнение", text)

    def test_specific_problem_does_not_need_extra_questions(self):
        problem = "машину трясет на холостых, чек мигает, на холодную сильнее"

        self.assertGreaterEqual(diagnostic_signal_score(problem), 2)
        self.assertFalse(needs_quick_clarification(problem))


if __name__ == "__main__":
    unittest.main()
