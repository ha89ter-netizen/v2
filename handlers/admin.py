from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from database import (
    get_admin_overview,
    get_bad_cached_responses,
    get_recent_api_errors,
    get_recent_users,
    get_top_problems,
    get_user_test_mode,
    set_user_test_mode,
)
from keyboards import admin_menu_keyboard, main_menu_keyboard
from services.admin_auth import admin_denied_text, is_admin
from services.api_stats import format_api_stats
from services.reminders import format_api_errors

router = Router()


def _money(value: float) -> str:
    return f"${value:.6f}"


def _clip(value: object, limit: int = 120) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"


async def _deny_if_needed(message: Message) -> bool:
    if is_admin(message.from_user.id):
        return False
    await message.answer(admin_denied_text())
    return True


def _format_overview(stats: dict) -> str:
    return (
        "Админ-сводка:\n\n"
        f"Пользователи: {stats['users']}\n"
        f"С домашним адресом: {stats['users_with_home']}\n"
        f"Авто в гаражах: {stats['cars']}\n"
        f"Обращения: {stats['issues']}\n"
        f"Опасные обращения: {stats['critical_issues']}\n"
        f"Поиски сервиса: {stats['service_searches']}\n"
        f"Активные напоминания: {stats['active_reminders']}\n"
        f"Кэш ответов: {stats['cache_entries']}\n"
        f"Плохой/отключённый кэш: {stats['bad_cache_entries']}\n"
        f"API-вызовы: {stats['api_calls']}\n"
        f"API-ошибки: {stats['api_errors']}\n"
        f"Примерная стоимость API: {_money(stats['api_cost'] or 0)}"
    )


def _format_users(rows: list) -> str:
    if not rows:
        return "Пользователей пока нет."

    lines = ["Последние пользователи:"]
    for user_id, username, language_code, has_home, cars_count, issues_count, last_issue_at in rows:
        name = f"@{username}" if username else "без username"
        home = "дом есть" if has_home else "дом нет"
        last = last_issue_at or "обращений нет"
        lines.append(
            f"{user_id} — {name}, {language_code or 'язык ?'}, "
            f"{home}, авто {cars_count}, обращений {issues_count}, последнее: {last}"
        )
    return "\n".join(lines)


def _format_top_problems(rows: list) -> str:
    if not rows:
        return "Частых проблем пока нет."

    lines = ["Частые проблемы:"]
    for problem, count, critical_count, last_created_at in rows:
        critical = f", опасных {critical_count}" if critical_count else ""
        lines.append(f"{count} раз{critical} — {_clip(problem)}\n   последнее: {last_created_at}")
    return "\n\n".join(lines)


def _format_bad_answers(rows: list) -> str:
    if not rows:
        return "Плохих ответов в кэше пока нет."

    lines = ["Ответы, которые надо проверить:"]
    for response_type, problem_key, vehicle_key, hits, helpful, not_helpful, disabled, updated_at in rows:
        status = "отключён" if disabled else "сомнительный"
        vehicle = f" | авто: {_clip(vehicle_key, 60)}" if vehicle_key else ""
        lines.append(
            f"{response_type}: {_clip(problem_key)}{vehicle}\n"
            f"   статус: {status}, показы: {hits}, 👍 {helpful}, 👎 {not_helpful}, обновлён: {updated_at}"
        )
    return "\n\n".join(lines)


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if await _deny_if_needed(message):
        return
    await message.answer(
        "Админка открыта. Выберите раздел 👇\n\n"
        "Команды: /admin_stats, /admin_users, /admin_problems, "
        "/admin_bad_answers, /admin_errors, /test_mode",
        reply_markup=admin_menu_keyboard(),
    )


@router.message(Command("admin_stats"))
@router.message(F.text == "📊 Админ статистика")
async def admin_stats(message: Message):
    if await _deny_if_needed(message):
        return
    await message.answer(_format_overview(await get_admin_overview()), reply_markup=admin_menu_keyboard())


@router.message(F.text == "💸 API расходы")
async def admin_api_costs(message: Message):
    if await _deny_if_needed(message):
        return
    await message.answer(await format_api_stats(), reply_markup=admin_menu_keyboard())


@router.message(Command("admin_errors"))
@router.message(F.text == "⚠️ API ошибки")
async def admin_errors(message: Message):
    if await _deny_if_needed(message):
        return
    await message.answer(format_api_errors(await get_recent_api_errors()), reply_markup=admin_menu_keyboard())


@router.message(Command("admin_users"))
@router.message(F.text == "👥 Пользователи")
async def admin_users(message: Message):
    if await _deny_if_needed(message):
        return
    await message.answer(_format_users(await get_recent_users()), reply_markup=admin_menu_keyboard())


@router.message(Command("admin_problems"))
@router.message(F.text == "🔧 Частые проблемы")
async def admin_problems(message: Message):
    if await _deny_if_needed(message):
        return
    await message.answer(_format_top_problems(await get_top_problems()), reply_markup=admin_menu_keyboard())


@router.message(Command("admin_bad_answers"))
@router.message(F.text == "👎 Плохие ответы")
async def admin_bad_answers(message: Message):
    if await _deny_if_needed(message):
        return
    await message.answer(_format_bad_answers(await get_bad_cached_responses()), reply_markup=admin_menu_keyboard())


@router.message(Command("test_mode"))
@router.message(F.text == "🧪 Тестовый режим")
async def toggle_test_mode(message: Message):
    if await _deny_if_needed(message):
        return
    current = await get_user_test_mode(message.from_user.id)
    await set_user_test_mode(message.from_user.id, not current)
    status = "включён" if not current else "выключен"
    await message.answer(
        f"Тестовый режим {status}.\n\n"
        "Когда он включён, бот показывает служебные детали поиска: категорию, радиус, рейтинг и локацию.",
        reply_markup=admin_menu_keyboard(),
    )


@router.message(Command("admin_close"))
async def admin_close(message: Message):
    if await _deny_if_needed(message):
        return
    await message.answer("Админка закрыта. Главное меню 👇", reply_markup=main_menu_keyboard())
