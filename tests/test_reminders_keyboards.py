import unittest

from tests._env import setup_test_env

setup_test_env()

from keyboards import diy_help_keyboard, fix_choice_keyboard, parts_after_result_keyboard, service_choice_keyboard, service_results_keyboard
from services.reminders import parse_reminder_text
from services.response_quality import improve_ai_answer
from services.service_categories import SERVICE_BUTTON_TO_CATEGORY, SERVICE_CATEGORIES
from services.vehicle_profile import format_vehicle_profile, parse_vehicle_profile


class ReminderKeyboardTests(unittest.TestCase):
    def test_parse_reminder_with_date_and_mileage(self):
        title, due_date, due_mileage, recurring_days, recurring_km = parse_reminder_text(
            "Замена масла | 2026-08-01 | 120000 км"
        )
        self.assertEqual(title, "Замена масла")
        self.assertEqual(due_date, "2026-08-01")
        self.assertEqual(due_mileage, 120000)
        self.assertIsNone(recurring_days)
        self.assertIsNone(recurring_km)

    def test_parse_reminder_keeps_unknown_parts_in_title(self):
        title, due_date, due_mileage, recurring_days, recurring_km = parse_reminder_text(
            "ТО | каждые 6 месяцев | 90000 км"
        )
        self.assertEqual(title, "ТО каждые 6 месяцев")
        self.assertEqual(due_date, "")
        self.assertEqual(due_mileage, 90000)
        self.assertIsNone(recurring_days)
        self.assertIsNone(recurring_km)

    def test_parse_recurring_reminder(self):
        title, due_date, due_mileage, recurring_days, recurring_km = parse_reminder_text(
            "Замена масла | 2026-08-01 | 120000 км | каждые 8000 км | каждые 180 дней"
        )
        self.assertEqual(title, "Замена масла")
        self.assertEqual(due_date, "2026-08-01")
        self.assertEqual(due_mileage, 120000)
        self.assertEqual(recurring_km, 8000)
        self.assertEqual(recurring_days, 180)

    def test_service_choice_keyboard_has_expected_categories(self):
        keyboard = service_choice_keyboard()
        labels = [button.text for row in keyboard.keyboard for button in row]
        for label in [
            "🚨 Эвакуатор",
            "🔧 СТО",
            "🏢 Дилерский центр",
            "🧰 Диагностика",
            "🛞 Шиномонтаж",
            "🔩 Запчасти",
            "⚡ Автоэлектрик",
            "🧱 Кузовной ремонт",
            "📐 Сход-развал",
            "🪟 Автостекла",
            "❄️ Кондиционер",
            "♻️ Авторазбор",
            "⛽ Заправка",
            "🧽 Автомойка",
        ]:
            with self.subTest(label=label):
                self.assertIn(label, labels)

    def test_service_buttons_are_mapped_to_known_categories(self):
        keyboard = service_choice_keyboard()
        labels = [button.text for row in keyboard.keyboard for button in row]
        for label in labels:
            with self.subTest(label=label):
                self.assertIn(label, SERVICE_BUTTON_TO_CATEGORY)
                self.assertIn(SERVICE_BUTTON_TO_CATEGORY[label], SERVICE_CATEGORIES)

    def test_post_diagnosis_and_repair_keyboards_have_followup_actions(self):
        fix_labels = [button.text for row in fix_choice_keyboard().keyboard for button in row]
        diy_labels = [button.text for row in diy_help_keyboard().keyboard for button in row]
        parts_labels = [button.text for row in parts_after_result_keyboard().keyboard for button in row]
        service_labels = [button.text for row in service_results_keyboard().keyboard for button in row]

        self.assertIn("🚦 Можно ли ехать?", fix_labels)
        self.assertIn("📜 Сохранить ремонт в историю", diy_labels)
        self.assertIn("🔩 Магазин запчастей рядом", parts_labels)
        self.assertIn("☎️ Контакты и маршрут", service_labels)

    def test_vehicle_profile_parser(self):
        profile = parse_vehicle_profile("Toyota Camry 2019 | 120000 км | 2.5 | автомат | бензин | Камри")
        self.assertEqual(profile.brand, "Toyota")
        self.assertEqual(profile.model, "Camry")
        self.assertEqual(profile.year, "2019")
        self.assertEqual(profile.mileage, 120000)
        self.assertEqual(profile.engine, "2.5")
        self.assertEqual(profile.transmission, "автомат")
        self.assertEqual(profile.fuel, "бензин")
        self.assertEqual(profile.nickname, "Камри")

    def test_format_vehicle_profile(self):
        row = (1, "", "Toyota", "Camry", "2019", 120000, "2.5", "автомат", "бензин", "Камри")
        self.assertIn("Камри", format_vehicle_profile(row))
        self.assertIn("пробег 120000 км", format_vehicle_profile(row))

    def test_response_quality_adds_practical_step_to_weak_answer(self):
        answer = improve_ai_answer("Может быть проблема с двигателем.", "diagnosis")
        self.assertIn("Практический минимум", answer)


if __name__ == "__main__":
    unittest.main()
