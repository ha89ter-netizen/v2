import tempfile
import unittest
from pathlib import Path

import aiosqlite
from aiogram.fsm.storage.base import StorageKey

from tests._env import setup_test_env

setup_test_env()

import database
from config import config
from services.admin_auth import admin_denied_text, is_admin
from services.sqlite_fsm_storage import SQLiteStorage


class DatabaseStorageTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmpdir.name) / "test.sqlite3")
        database.DB_PATH = self.db_path
        await database.init_db()

    async def asyncTearDown(self):
        self.tmpdir.cleanup()

    async def test_user_issue_cache_feedback_reminder_and_reset_flow(self):
        await database.add_user(123, "tester", "ru")
        await database.save_home_location(123, 0.0, 0.0, "Нулевая точка")
        self.assertEqual(await database.get_home_location(123), (0.0, 0.0, "Нулевая точка"))

        await database.add_car(123, "", "Toyota", "Camry", "2019")
        cars = await database.get_cars(123)
        self.assertEqual(len(cars), 1)
        self.assertEqual((await database.get_car_details(123, cars[0][0]))[3], "Camry")

        issue_id = await database.create_issue(123, "горит чек", vehicle="Toyota Camry 2019")
        updated = await database.update_issue(issue_id, 123, status="diagnosed", diagnosis="Проверить сканером")
        self.assertTrue(updated)
        self.assertEqual(len(await database.get_recent_issues(123)), 1)

        await database.save_cached_response("diagnosis", "горит чек", "Ответ", "Toyota Camry 2019")
        self.assertEqual(
            await database.get_cached_response("diagnosis", "горит чек", "Toyota Camry 2019"),
            "Ответ",
        )
        await database.save_response_feedback(123, "diagnosis", "горит чек", False, "Toyota Camry 2019")
        await database.save_response_feedback(123, "diagnosis", "горит чек", False, "Toyota Camry 2019")
        self.assertTrue(await database.has_negative_feedback("diagnosis", "горит чек", "Toyota Camry 2019"))
        self.assertIsNone(await database.get_cached_response("diagnosis", "горит чек", "Toyota Camry 2019"))

        reminder_id = await database.add_reminder(
            123,
            "Замена масла",
            due_date="2026-08-01",
            due_mileage=120000,
            recurring_interval_days=180,
            recurring_interval_km=8000,
        )
        self.assertEqual(len(await database.get_reminders(123)), 1)

        overview = await database.get_admin_overview()
        self.assertEqual(overview["users"], 1)
        self.assertEqual(overview["users_with_home"], 1)
        self.assertEqual(overview["cars"], 1)
        self.assertEqual(overview["issues"], 1)
        self.assertEqual(overview["active_reminders"], 1)
        self.assertEqual(overview["bad_cache_entries"], 1)
        self.assertEqual(len(await database.get_recent_users()), 1)
        self.assertEqual((await database.get_top_problems())[0][0], "горит чек")
        self.assertEqual(len(await database.get_bad_cached_responses()), 1)

        self.assertTrue(await database.complete_reminder(123, reminder_id))
        reminders = await database.get_reminders(123)
        self.assertEqual(len(reminders), 1)
        self.assertEqual(reminders[0][2], "2027-01-28")
        self.assertEqual(reminders[0][3], 128000)

        storage = SQLiteStorage(self.db_path)
        key = StorageKey(bot_id=1, chat_id=123, user_id=123)
        await storage.set_state(key, "UserFlow:testing")
        await storage.set_data(key, {"problem": "test"})

        await database.clear_user_data(123)
        self.assertEqual(await database.get_cars(123), [])
        self.assertEqual(await database.get_recent_issues(123), [])
        self.assertIsNone(await database.get_home_location(123))
        self.assertIsNone(await storage.get_state(key))
        self.assertEqual(await storage.get_data(key), {})

    async def test_admin_auth_requires_configured_admin_id(self):
        original_admin_ids = config.ADMIN_IDS
        try:
            config.ADMIN_IDS = set()
            self.assertFalse(is_admin(123))
            self.assertIn("выключена", admin_denied_text())

            config.ADMIN_IDS = {123}
            self.assertTrue(is_admin(123))
            self.assertFalse(is_admin(456))
        finally:
            config.ADMIN_IDS = original_admin_ids

    async def test_api_usage_summary_records_success_and_failure(self):
        await database.record_api_usage("openai", "diagnosis", True, attempts=1, total_tokens=10)
        await database.record_api_usage("openai", "diagnosis", False, attempts=2, error="timeout")

        summary = await database.get_api_usage_summary()
        self.assertEqual(summary[0][0], "openai")
        self.assertEqual(summary[0][1], "diagnosis")
        self.assertEqual(summary[0][2], 2)
        self.assertEqual(summary[0][3], 1)
        self.assertEqual(summary[0][4], 1)


class SQLiteStorageTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmpdir.name) / "fsm.sqlite3")

    async def asyncTearDown(self):
        self.tmpdir.cleanup()

    async def test_state_and_data_survive_storage_reopen(self):
        key = StorageKey(bot_id=1, chat_id=10, user_id=20)
        storage = SQLiteStorage(self.db_path)
        await storage.set_state(key, "UserFlow:waiting_for_problem")
        await storage.set_data(key, {"vehicle": "Toyota Camry 2019"})

        reopened = SQLiteStorage(self.db_path)
        self.assertEqual(await reopened.get_state(key), "UserFlow:waiting_for_problem")
        self.assertEqual(await reopened.get_data(key), {"vehicle": "Toyota Camry 2019"})

        await reopened.set_state(key, None)
        await reopened.set_data(key, {})
        self.assertIsNone(await reopened.get_state(key))
        self.assertEqual(await reopened.get_data(key), {})


if __name__ == "__main__":
    unittest.main()
