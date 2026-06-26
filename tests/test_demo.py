import unittest

from tests._env import setup_test_env

setup_test_env()

from keyboards import demo_keyboard
from services.demo import DEMO_MENU_TEXT, demo_labels, get_demo_text


class DemoTests(unittest.TestCase):
    def test_demo_menu_has_all_scenarios(self):
        labels = demo_labels()
        keyboard_labels = [button.text for row in demo_keyboard().keyboard for button in row]

        self.assertIn("безопасная витрина MVP", DEMO_MENU_TEXT)
        self.assertGreaterEqual(len(labels), 5)
        for label in labels:
            with self.subTest(label=label):
                self.assertIn(label, keyboard_labels)
                self.assertNotEqual(get_demo_text(label), DEMO_MENU_TEXT)

    def test_unknown_demo_label_returns_menu_text(self):
        self.assertEqual(get_demo_text("unknown"), DEMO_MENU_TEXT)


if __name__ == "__main__":
    unittest.main()
