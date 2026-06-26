import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import config
from database import DB_PATH, init_db
from handlers import admin, common, problem, location, vehicle, photo, parts, help_flow
from services.reminder_scheduler import reminder_worker
from services.sqlite_fsm_storage import SQLiteStorage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    await init_db()

    bot = Bot(token=config.TELEGRAM_TOKEN)
    dp = Dispatcher(storage=SQLiteStorage(DB_PATH))

    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(problem.router)
    dp.include_router(location.router)
    dp.include_router(vehicle.router)
    dp.include_router(photo.router)
    dp.include_router(parts.router)
    dp.include_router(help_flow.router)

    logger.info("AutoBot v2 started")
    reminder_task = asyncio.create_task(reminder_worker(bot))
    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        reminder_task.cancel()
        try:
            await reminder_task
        except asyncio.CancelledError:
            pass
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
