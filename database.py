import aiosqlite
import logging

logger = logging.getLogger(__name__)
DB_PATH = "autobot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                language_code TEXT,
                home_lat REAL,
                home_lon REAL,
                home_address TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                vin TEXT,
                brand TEXT,
                model TEXT,
                year TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        await db.commit()
    logger.info("База данных готова!")

async def add_user(user_id: int, username: str, language_code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (user_id, username, language_code)
            VALUES (?, ?, ?)
        """, (user_id, username, language_code))
        await db.commit()

async def add_car(user_id: int, vin: str, brand: str, model: str, year: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO cars (user_id, vin, brand, model, year)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, vin, brand, model, year))
        await db.commit()

async def get_cars(user_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT id, vin, brand, model, year FROM cars WHERE user_id = ?
        """, (user_id,)) as cursor:
            return await cursor.fetchall()

async def delete_car(car_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM cars WHERE id = ?", (car_id,))
        await db.commit()

async def save_home_location(user_id: int, lat: float, lon: float, address: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users SET home_lat=?, home_lon=?, home_address=?
            WHERE user_id=?
        """, (lat, lon, address, user_id))
        await db.commit()

async def get_home_location(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT home_lat, home_lon, home_address FROM users WHERE user_id=?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                return row[0], row[1], row[2]
            return None

