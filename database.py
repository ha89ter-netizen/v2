import logging
import os
from typing import Optional
from datetime import datetime, timedelta

import aiosqlite

from utils import normalize_text_key

logger = logging.getLogger(__name__)
DB_PATH = os.getenv("DB_PATH", "autobot.db")

async def _ensure_column(db, table: str, column: str, definition: str) -> None:
    async with db.execute(f"PRAGMA table_info({table})") as cursor:
        columns = [row[1] for row in await cursor.fetchall()]
    if column not in columns:
        await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                language_code TEXT,
                home_lat REAL,
                home_lon REAL,
                home_address TEXT,
                test_mode INTEGER DEFAULT 0
            )
        """)
        await _ensure_column(db, "users", "test_mode", "INTEGER DEFAULT 0")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                vin TEXT,
                brand TEXT,
                model TEXT,
                year TEXT,
                mileage INTEGER,
                engine TEXT,
                transmission TEXT,
                fuel TEXT,
                nickname TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        await _ensure_column(db, "cars", "mileage", "INTEGER")
        await _ensure_column(db, "cars", "engine", "TEXT")
        await _ensure_column(db, "cars", "transmission", "TEXT")
        await _ensure_column(db, "cars", "fuel", "TEXT")
        await _ensure_column(db, "cars", "nickname", "TEXT")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                car_id INTEGER,
                problem TEXT NOT NULL,
                vehicle TEXT,
                initial_advice TEXT,
                diagnosis TEXT,
                risk_level TEXT DEFAULT 'normal',
                status TEXT DEFAULT 'new',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (car_id) REFERENCES cars(id)
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_issues_user_created
            ON issues(user_id, created_at)
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ai_response_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_type TEXT NOT NULL,
                problem_key TEXT NOT NULL,
                vehicle_key TEXT NOT NULL DEFAULT '',
                response TEXT NOT NULL,
                hits INTEGER DEFAULT 0,
                helpful INTEGER DEFAULT 0,
                not_helpful INTEGER DEFAULT 0,
                disabled INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(response_type, problem_key, vehicle_key)
            )
        """)
        await _ensure_column(db, "ai_response_cache", "helpful", "INTEGER DEFAULT 0")
        await _ensure_column(db, "ai_response_cache", "not_helpful", "INTEGER DEFAULT 0")
        await _ensure_column(db, "ai_response_cache", "disabled", "INTEGER DEFAULT 0")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ai_response_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                response_type TEXT NOT NULL,
                problem_key TEXT NOT NULL,
                vehicle_key TEXT NOT NULL DEFAULT '',
                helpful INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                operation TEXT NOT NULL,
                model TEXT,
                success INTEGER NOT NULL,
                attempts INTEGER DEFAULT 1,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                estimated_cost_usd REAL DEFAULT 0,
                error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_usage_provider_created
            ON api_usage(provider, created_at)
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                car_id INTEGER,
                title TEXT NOT NULL,
                due_date TEXT,
                due_mileage INTEGER,
                recurring_interval_days INTEGER,
                recurring_interval_km INTEGER,
                status TEXT DEFAULT 'active',
                notified_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (car_id) REFERENCES cars(id)
            )
        """)
        await _ensure_column(db, "reminders", "notified_at", "TEXT")
        await _ensure_column(db, "reminders", "recurring_interval_days", "INTEGER")
        await _ensure_column(db, "reminders", "recurring_interval_km", "INTEGER")
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_reminders_user_status
            ON reminders(user_id, status)
        """)
        await db.commit()
    logger.info("База данных готова!")

async def add_user(user_id: int, username: str, language_code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, language_code)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                language_code = excluded.language_code
        """, (user_id, username, language_code))
        await db.commit()

async def set_user_test_mode(user_id: int, enabled: bool) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, language_code, test_mode)
            VALUES (?, '', 'ru', ?)
            ON CONFLICT(user_id) DO UPDATE SET test_mode = excluded.test_mode
        """, (user_id, 1 if enabled else 0))
        await db.commit()

async def get_user_test_mode(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT test_mode FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return bool(row and row[0])

async def add_car(
    user_id: int,
    vin: str,
    brand: str,
    model: str,
    year: str,
    mileage: Optional[int] = None,
    engine: str = "",
    transmission: str = "",
    fuel: str = "",
    nickname: str = "",
):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO cars (
                user_id, vin, brand, model, year,
                mileage, engine, transmission, fuel, nickname
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, vin, brand, model, year, mileage, engine, transmission, fuel, nickname))
        await db.commit()

async def get_cars(user_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT id, vin, brand, model, year FROM cars WHERE user_id = ?
        """, (user_id,)) as cursor:
                return await cursor.fetchall()

async def get_car_details(user_id: int, car_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT id, vin, brand, model, year, mileage, engine, transmission, fuel, nickname
            FROM cars
            WHERE id = ? AND user_id = ?
        """, (car_id, user_id)) as cursor:
            return await cursor.fetchone()

async def delete_car(user_id: int, car_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM cars WHERE id = ? AND user_id = ?",
            (car_id, user_id),
        )
        await db.commit()
        return cursor.rowcount > 0

async def save_home_location(user_id: int, lat: float, lon: float, address: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, language_code, home_lat, home_lon, home_address)
            VALUES (?, '', 'ru', ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                home_lat = excluded.home_lat,
                home_lon = excluded.home_lon,
                home_address = excluded.home_address
        """, (user_id, lat, lon, address))
        await db.commit()

async def get_home_location(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT home_lat, home_lon, home_address FROM users WHERE user_id=?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0] is not None and row[1] is not None:
                return row[0], row[1], row[2]
            return None

async def create_issue(
    user_id: int,
    problem: str,
    vehicle: str = "",
    car_id: Optional[int] = None,
    risk_level: str = "normal",
    status: str = "new",
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO issues (user_id, car_id, problem, vehicle, risk_level, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, car_id, problem, vehicle, risk_level, status))
        await db.commit()
        return cursor.lastrowid

async def update_issue(issue_id: int, user_id: int, **fields) -> bool:
    allowed = {
        "car_id",
        "vehicle",
        "initial_advice",
        "diagnosis",
        "risk_level",
        "status",
    }
    updates = {key: value for key, value in fields.items() if key in allowed}
    if not updates:
        return False

    set_clause = ", ".join(f"{key} = ?" for key in updates)
    values = list(updates.values()) + [issue_id, user_id]

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(f"""
            UPDATE issues
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        """, values)
        await db.commit()
        return cursor.rowcount > 0

async def get_recent_issues(user_id: int, limit: int = 5) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT id, problem, vehicle, risk_level, status, created_at
            FROM issues
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit)) as cursor:
            return await cursor.fetchall()

async def get_cached_response(response_type: str, problem: str, vehicle: str = "") -> Optional[str]:
    problem_key = normalize_text_key(problem)
    vehicle_key = normalize_text_key(vehicle)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT id, response
            FROM ai_response_cache
            WHERE response_type = ? AND problem_key = ? AND vehicle_key = ?
              AND disabled = 0
              AND NOT (not_helpful >= 2 AND not_helpful > helpful)
        """, (response_type, problem_key, vehicle_key)) as cursor:
            row = await cursor.fetchone()

        if not row:
            return None

        await db.execute("""
            UPDATE ai_response_cache
            SET hits = hits + 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (row[0],))
        await db.commit()
        return row[1]

async def save_cached_response(
    response_type: str,
    problem: str,
    response: str,
    vehicle: str = "",
) -> None:
    problem_key = normalize_text_key(problem)
    vehicle_key = normalize_text_key(vehicle)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO ai_response_cache (response_type, problem_key, vehicle_key, response)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(response_type, problem_key, vehicle_key)
            DO UPDATE SET response = excluded.response, updated_at = CURRENT_TIMESTAMP
        """, (response_type, problem_key, vehicle_key, response))
        await db.commit()

async def save_response_feedback(
    user_id: int,
    response_type: str,
    problem: str,
    helpful: bool,
    vehicle: str = "",
) -> None:
    problem_key = normalize_text_key(problem)
    vehicle_key = normalize_text_key(vehicle)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO ai_response_feedback (
                user_id, response_type, problem_key, vehicle_key, helpful
            )
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, response_type, problem_key, vehicle_key, 1 if helpful else 0))

        field = "helpful" if helpful else "not_helpful"
        await db.execute(f"""
            UPDATE ai_response_cache
            SET {field} = {field} + 1,
                disabled = CASE
                    WHEN ? = 0 AND not_helpful + 1 >= 2 AND not_helpful + 1 > helpful
                    THEN 1
                    ELSE disabled
                END,
                updated_at = CURRENT_TIMESTAMP
            WHERE response_type = ? AND problem_key = ? AND vehicle_key = ?
        """, (1 if helpful else 0, response_type, problem_key, vehicle_key))
        await db.commit()

async def has_negative_feedback(
    response_type: str,
    problem: str,
    vehicle: str = "",
) -> bool:
    problem_key = normalize_text_key(problem)
    vehicle_key = normalize_text_key(vehicle)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT
                SUM(CASE WHEN helpful = 1 THEN 1 ELSE 0 END) AS helpful_count,
                SUM(CASE WHEN helpful = 0 THEN 1 ELSE 0 END) AS not_helpful_count
            FROM ai_response_feedback
            WHERE response_type = ? AND problem_key = ? AND vehicle_key = ?
        """, (response_type, problem_key, vehicle_key)) as cursor:
            row = await cursor.fetchone()

    helpful_count = row[0] or 0
    not_helpful_count = row[1] or 0
    return not_helpful_count >= 2 and not_helpful_count > helpful_count

async def record_api_usage(
    provider: str,
    operation: str,
    success: bool,
    attempts: int = 1,
    model: str = "",
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    estimated_cost_usd: float = 0.0,
    error: str = "",
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO api_usage (
                provider, operation, model, success, attempts,
                prompt_tokens, completion_tokens, total_tokens,
                estimated_cost_usd, error
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            provider,
            operation,
            model,
            1 if success else 0,
            attempts,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            estimated_cost_usd,
            error[:500],
        ))
        await db.commit()

async def get_api_usage_summary() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT
                provider,
                operation,
                COUNT(*) AS calls,
                SUM(success) AS successes,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) AS failures,
                SUM(attempts) AS attempts,
                SUM(prompt_tokens) AS prompt_tokens,
                SUM(completion_tokens) AS completion_tokens,
                SUM(total_tokens) AS total_tokens,
                SUM(estimated_cost_usd) AS estimated_cost_usd
            FROM api_usage
            GROUP BY provider, operation
            ORDER BY provider, operation
        """) as cursor:
            return await cursor.fetchall()

async def get_recent_api_errors(limit: int = 10) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT provider, operation, model, attempts, error, created_at
            FROM api_usage
            WHERE success = 0
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,)) as cursor:
            return await cursor.fetchall()

async def get_admin_overview() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async def scalar(query: str, params: tuple = ()):
            async with db.execute(query, params) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

        return {
            "users": await scalar("SELECT COUNT(*) FROM users"),
            "users_with_home": await scalar("""
                SELECT COUNT(*) FROM users
                WHERE home_lat IS NOT NULL AND home_lon IS NOT NULL
            """),
            "cars": await scalar("SELECT COUNT(*) FROM cars"),
            "issues": await scalar("SELECT COUNT(*) FROM issues"),
            "critical_issues": await scalar("""
                SELECT COUNT(*) FROM issues WHERE risk_level = 'critical'
            """),
            "service_searches": await scalar("""
                SELECT COUNT(*) FROM issues WHERE status = 'searching_service'
            """),
            "active_reminders": await scalar("""
                SELECT COUNT(*) FROM reminders WHERE status = 'active'
            """),
            "cache_entries": await scalar("""
                SELECT COUNT(*) FROM ai_response_cache WHERE disabled = 0
            """),
            "bad_cache_entries": await scalar("""
                SELECT COUNT(*) FROM ai_response_cache
                WHERE disabled = 1 OR not_helpful > helpful
            """),
            "api_calls": await scalar("SELECT COUNT(*) FROM api_usage"),
            "api_errors": await scalar("""
                SELECT COUNT(*) FROM api_usage WHERE success = 0
            """),
            "api_cost": await scalar("""
                SELECT COALESCE(SUM(estimated_cost_usd), 0) FROM api_usage
            """),
        }

async def get_recent_users(limit: int = 10) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT
                u.user_id,
                u.username,
                u.language_code,
                CASE
                    WHEN u.home_lat IS NOT NULL AND u.home_lon IS NOT NULL THEN 1
                    ELSE 0
                END AS has_home,
                COUNT(DISTINCT c.id) AS cars_count,
                COUNT(DISTINCT i.id) AS issues_count,
                MAX(i.created_at) AS last_issue_at
            FROM users u
            LEFT JOIN cars c ON c.user_id = u.user_id
            LEFT JOIN issues i ON i.user_id = u.user_id
            GROUP BY u.user_id
            ORDER BY last_issue_at DESC, u.user_id DESC
            LIMIT ?
        """, (limit,)) as cursor:
            return await cursor.fetchall()

async def get_top_problems(limit: int = 10) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT
                problem,
                COUNT(*) AS count,
                SUM(CASE WHEN risk_level = 'critical' THEN 1 ELSE 0 END) AS critical_count,
                MAX(created_at) AS last_created_at
            FROM issues
            GROUP BY lower(trim(problem))
            ORDER BY count DESC, last_created_at DESC
            LIMIT ?
        """, (limit,)) as cursor:
            return await cursor.fetchall()

async def get_bad_cached_responses(limit: int = 10) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT
                response_type,
                problem_key,
                vehicle_key,
                hits,
                helpful,
                not_helpful,
                disabled,
                updated_at
            FROM ai_response_cache
            WHERE disabled = 1 OR not_helpful > helpful
            ORDER BY disabled DESC, not_helpful DESC, updated_at DESC
            LIMIT ?
        """, (limit,)) as cursor:
            return await cursor.fetchall()

async def add_reminder(
    user_id: int,
    title: str,
    due_date: str = "",
    due_mileage: Optional[int] = None,
    car_id: Optional[int] = None,
    recurring_interval_days: Optional[int] = None,
    recurring_interval_km: Optional[int] = None,
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO reminders (
                user_id, car_id, title, due_date, due_mileage,
                recurring_interval_days, recurring_interval_km
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            car_id,
            title,
            due_date,
            due_mileage,
            recurring_interval_days,
            recurring_interval_km,
        ))
        await db.commit()
        return cursor.lastrowid

async def get_reminders(user_id: int, include_done: bool = False) -> list:
    status_clause = "" if include_done else "AND status = 'active'"
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(f"""
            SELECT
                id, title, due_date, due_mileage, status, created_at,
                recurring_interval_days, recurring_interval_km
            FROM reminders
            WHERE user_id = ? {status_clause}
            ORDER BY
                CASE WHEN due_date IS NULL OR due_date = '' THEN 1 ELSE 0 END,
                due_date,
                id DESC
        """, (user_id,)) as cursor:
            return await cursor.fetchall()

async def complete_reminder(user_id: int, reminder_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT title, due_date, due_mileage, car_id,
                   recurring_interval_days, recurring_interval_km
            FROM reminders
            WHERE id = ? AND user_id = ? AND status = 'active'
        """, (reminder_id, user_id)) as cursor:
            row = await cursor.fetchone()
        if not row:
            return False

        cursor = await db.execute("""
            UPDATE reminders
            SET status = 'done', completed_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ? AND status = 'active'
        """, (reminder_id, user_id))
        title, due_date, due_mileage, car_id, recurring_days, recurring_km = row
        next_due_date = ""
        next_due_mileage = None

        if recurring_days and due_date:
            try:
                next_due_date = (
                    datetime.strptime(due_date, "%Y-%m-%d").date()
                    + timedelta(days=int(recurring_days))
                ).isoformat()
            except ValueError:
                next_due_date = ""
        if recurring_km and due_mileage:
            next_due_mileage = int(due_mileage) + int(recurring_km)

        if next_due_date or next_due_mileage:
            await db.execute("""
                INSERT INTO reminders (
                    user_id, car_id, title, due_date, due_mileage,
                    recurring_interval_days, recurring_interval_km
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                car_id,
                title,
                next_due_date,
                next_due_mileage,
                recurring_days,
                recurring_km,
            ))
        await db.commit()
        return cursor.rowcount > 0

async def get_due_reminders(today: str) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT id, user_id, title, due_date, due_mileage
            FROM reminders
            WHERE status = 'active'
              AND due_date IS NOT NULL
              AND due_date != ''
              AND due_date <= ?
              AND (notified_at IS NULL OR date(notified_at) < date(?))
            ORDER BY due_date, id
        """, (today, today)) as cursor:
            return await cursor.fetchall()

async def mark_reminder_notified(reminder_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE reminders
            SET notified_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (reminder_id,))
        await db.commit()

async def clear_user_data(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("DELETE FROM ai_response_feedback WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM reminders WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM issues WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM cars WHERE user_id = ?", (user_id,))
        await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

        async with db.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'fsm_storage'
        """) as cursor:
            has_fsm_storage = await cursor.fetchone()
        if has_fsm_storage:
            await db.execute("DELETE FROM fsm_storage WHERE user_id = ?", (user_id,))

        await db.commit()
