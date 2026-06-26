import unittest

from tests._env import setup_test_env

setup_test_env()

from keyboards import main_menu_keyboard
from services.i18n import info_text, is_english, start_text


class I18nTests(unittest.TestCase):
    def test_detects_english_language_code(self):
        self.assertTrue(is_english("en"))
        self.assertTrue(is_english("en-US"))
        self.assertFalse(is_english("ru"))

    def test_start_text_uses_english_for_english_users(self):
        text = start_text("Alan", "en")

        self.assertIn("Hello, Alan", text)
        self.assertIn("personal AI car assistant", text)

    def test_info_text_uses_english_for_english_users(self):
        self.assertIn("Here is what I can do", info_text("en"))
        self.assertIn("Вот что я умею", info_text("ru"))

    def test_main_menu_uses_english_buttons_for_english_users(self):
        labels = [button.text for row in main_menu_keyboard("en").keyboard for button in row]

        self.assertIn("🔧 Describe problem", labels)
        self.assertIn("🔩 Find part", labels)
        self.assertIn("📍 Find service nearby", labels)
        self.assertIn("ℹ️ What can you do", labels)


if __name__ == "__main__":
    unittest.main()
