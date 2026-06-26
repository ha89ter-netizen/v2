import asyncio
import logging
from datetime import date
from typing import Optional

from aiogram import Bot

from config import config
from database import get_due_reminders, mark_reminder_notified

logger = logging.getLogger(__name__)


def _format_due_reminder(title: str, due_date: str, due_mileage: Optional[int]) -> str:
    parts = [f"Напоминание: {title}"]
    if due_date:
        parts.append(f"Дата: {due_date}")
    if due_mileage:
        parts.append(f"Пробег: {due_mileage} км")
    parts.append("")
    parts.append("Если уже сделали — закройте: /done_reminder ID")
    return "\n".join(parts)


async def send_due_reminders(bot: Bot) -> int:
    today = date.today().isoformat()
    reminders = await get_due_reminders(today)
    sent = 0

    for reminder_id, user_id, title, due_date, due_mileage in reminders:
        try:
            text = _format_due_reminder(title, due_date, due_mileage).replace(
                "/done_reminder ID",
                f"/done_reminder {reminder_id}",
            )
            await bot.send_message(user_id, text)
            await mark_reminder_notified(reminder_id)
            sent += 1
        except Exception as exc:
            logger.warning("Не удалось отправить напоминание %s: %s", reminder_id, exc)

    return sent


async def reminder_worker(bot: Bot) -> None:
    while True:
        try:
            sent = await send_due_reminders(bot)
            if sent:
                logger.info("Отправлено напоминаний: %s", sent)
        except Exception:
            logger.exception("Ошибка проверки напоминаний")

        await asyncio.sleep(config.REMINDER_CHECK_INTERVAL_SECONDS)
