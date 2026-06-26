from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states import UserFlow
from keyboards import demo_keyboard, main_menu_keyboard, garage_keyboard, vin_skip_keyboard
from config import config
from database import (
    add_reminder,
    add_user,
    clear_user_data,
    complete_reminder,
    delete_car,
    get_car_details,
    get_cars,
    get_recent_api_errors,
    get_recent_issues,
    get_reminders,
    save_response_feedback,
)
from services.api_stats import format_api_stats
from services.admin_auth import admin_denied_text, is_admin
from services.demo import all_demo_labels, demo_menu_text, get_demo_text
from services.i18n import info_text, is_english, phone_launcher_text, start_text, user_language_code
from services.reminders import format_api_errors, format_reminders, parse_reminder_text
from services.vehicle_profile import format_vehicle_profile
from utils import escape_markdown

router = Router()

INFO_TEXT = info_text("ru")

def _format_history(issues: list, language_code: str = "") -> str:
    english = is_english(language_code)
    if not issues:
        return "History is empty. Describe your first problem and I will save it here." if english else "История пока пустая. Опишите первую проблему, и я сохраню её здесь."

    status_labels = {
        "new": "новая",
        "initial_advice": "первичный совет",
        "diagnosed": "диагноз готов",
        "diy": "самостоятельный ремонт",
        "fixed": "починено",
        "needs_service": "нужен сервис",
        "searching_service": "поиск сервиса",
        "safety_escalated": "опасный случай",
        "diy_blocked": "DIY заблокирован",
        "photo_received": "фото получено",
        "photo_analyzed": "фото проанализировано",
        "diy_stuck": "ремонт не получился",
        "diy_saved": "ремонт сохранён",
        "parts_selected": "запчасть подобрана",
    }
    status_labels_en = {
        "new": "new",
        "initial_advice": "initial advice",
        "diagnosed": "diagnosed",
        "diy": "DIY repair",
        "fixed": "fixed",
        "needs_service": "needs service",
        "searching_service": "searching service",
        "safety_escalated": "dangerous case",
        "diy_blocked": "DIY blocked",
        "photo_received": "photo received",
        "photo_analyzed": "photo analyzed",
        "diy_stuck": "DIY stuck",
        "diy_saved": "repair saved",
        "parts_selected": "part selected",
    }
    lines = ["Recent cases:" if english else "Последние обращения:"]
    for issue_id, problem, vehicle, risk_level, status, created_at in issues:
        risk = ("dangerous" if risk_level == "critical" else "normal") if english else ("опасно" if risk_level == "critical" else "обычно")
        vehicle_text = (f"\n   Vehicle: {vehicle}" if vehicle else "") if english else (f"\n   Авто: {vehicle}" if vehicle else "")
        labels = status_labels_en if english else status_labels
        lines.append(
            f"{issue_id}. {problem}{vehicle_text}\n"
            + (f"   Status: {labels.get(status, status)} | Risk: {risk} | {created_at}" if english else f"   Статус: {labels.get(status, status)} | Риск: {risk} | {created_at}")
        )
    return "\n\n".join(lines)

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    await state.clear()
    await add_user(
        message.from_user.id,
        message.from_user.username or "",
        language_code
    )
    await state.set_state(UserFlow.main_menu)
    await message.answer(
        start_text(message.from_user.first_name, language_code),
        reply_markup=main_menu_keyboard(language_code),
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(info_text(user_language_code(message.from_user)))

@router.message(Command("demo"))
async def cmd_demo(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    await state.clear()
    await state.set_state(UserFlow.main_menu)
    await message.answer(demo_menu_text(language_code), reply_markup=demo_keyboard(language_code))

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(UserFlow.main_menu)
    language_code = user_language_code(message.from_user)
    text = "Current flow was reset. Main menu 👇" if language_code.startswith("en") else "Текущий сценарий сброшен. Главное меню 👇"
    await message.answer(text, reply_markup=main_menu_keyboard(language_code))

@router.message(Command("reset_me"))
async def cmd_reset_me(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    await state.clear()
    await clear_user_data(message.from_user.id)
    await message.answer(
        "Done. I forgot your cars, history, reminders, home address, and current flow.\n\nYou can start testing again: /start"
        if is_english(language_code)
        else "Готово. Я забыл ваши машины, историю, напоминания, домашний адрес и текущий сценарий.\n\nМожно начинать тест заново: /start"
    )

@router.message(Command("garage"))
async def cmd_garage(message: Message, state: FSMContext):
    await btn_garage(message, state)

@router.message(Command("history"))
async def cmd_history(message: Message):
    issues = await get_recent_issues(message.from_user.id)
    await message.answer(_format_history(issues, user_language_code(message.from_user)))

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(admin_denied_text())
        return
    await message.answer(await format_api_stats())

@router.message(Command("errors"))
async def cmd_errors(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(admin_denied_text())
        return
    errors = await get_recent_api_errors()
    await message.answer(format_api_errors(errors))

@router.message(Command("reminders"))
async def cmd_reminders(message: Message):
    await add_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.language_code or "ru",
    )
    reminders = await get_reminders(message.from_user.id)
    await message.answer(format_reminders(reminders))

@router.message(Command("add_reminder"))
async def cmd_add_reminder(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    await state.set_state(UserFlow.waiting_for_reminder)
    await message.answer(
        (
            "Write a reminder in this format:\n"
            "Oil change | 2026-08-01 | 120000 km\n\n"
            "You can specify only text, date, or mileage."
        )
        if is_english(language_code)
        else "Напишите напоминание в формате:\nЗамена масла | 2026-08-01 | 120000 км\n\nМожно указать только текст, дату или пробег."
    )

@router.message(Command("done_reminder"))
async def cmd_done_reminder(message: Message):
    language_code = user_language_code(message.from_user)
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        await message.answer("Specify ID: /done_reminder 3" if is_english(language_code) else "Укажите ID: /done_reminder 3")
        return
    done = await complete_reminder(message.from_user.id, int(parts[1].strip()))
    await message.answer(("Reminder completed." if done else "Active reminder not found.") if is_english(language_code) else ("Напоминание закрыто." if done else "Активное напоминание не найдено."))

@router.message(F.text.in_({"ℹ️ Что умеет бот", "ℹ️ What can you do"}))
async def btn_info(message: Message):
    await message.answer(info_text(user_language_code(message.from_user)))

@router.message(F.text.in_({"📱 На телефон", "📱 Add to phone"}))
async def btn_phone_launcher(message: Message):
    await message.answer(phone_launcher_text(user_language_code(message.from_user)))

@router.message(F.text.in_(set(all_demo_labels())))
async def btn_demo_scenario(message: Message):
    language_code = user_language_code(message.from_user)
    await message.answer(get_demo_text(message.text, language_code), reply_markup=demo_keyboard(language_code))

@router.message(F.text.in_({"📜 История", "📜 History"}))
async def btn_history(message: Message):
    issues = await get_recent_issues(message.from_user.id)
    await message.answer(_format_history(issues, user_language_code(message.from_user)))

@router.message(F.text.in_({"⏰ Напоминания", "⏰ Reminders"}))
async def btn_reminders(message: Message):
    await add_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.language_code or "ru",
    )
    reminders = await get_reminders(message.from_user.id)
    await message.answer(format_reminders(reminders))

@router.message(UserFlow.waiting_for_reminder, F.text)
async def receive_reminder(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    title, due_date, due_mileage, recurring_days, recurring_km = parse_reminder_text(message.text)
    if len(title) < 2:
        await message.answer("Write the reminder title in more detail." if is_english(language_code) else "Напишите название напоминания подробнее.")
        return
    await add_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.language_code or "ru",
    )
    await add_reminder(
        user_id=message.from_user.id,
        title=title,
        due_date=due_date,
        due_mileage=due_mileage,
        recurring_interval_days=recurring_days,
        recurring_interval_km=recurring_km,
    )
    await state.set_state(UserFlow.main_menu)
    await message.answer("Reminder saved." if is_english(language_code) else "Напоминание сохранено.", reply_markup=main_menu_keyboard(language_code))

@router.message(F.text.in_({"🏠 Главное меню", "🏠 Main menu"}))
async def btn_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(UserFlow.main_menu)
    language_code = user_language_code(message.from_user)
    text = "Main menu 👇" if language_code.startswith("en") else "Главное меню 👇"
    await message.answer(text, reply_markup=main_menu_keyboard(language_code))

@router.message(F.text.in_({"🔧 Новая проблема", "🔧 New problem"}))
async def btn_new_problem(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    await state.clear()
    await state.set_state(UserFlow.waiting_for_problem)
    await state.update_data(language_code=language_code)
    await message.answer("Describe what happened with the car 👇" if is_english(language_code) else "Опишите что случилось с автомобилем 👇")

@router.message(F.text.in_({"🚗 Гараж", "🚗 Мой гараж", "🚗 Garage", "🚗 My garage"}))
async def btn_garage(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    await add_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.language_code or "ru",
    )
    await state.set_state(UserFlow.garage)
    cars = await get_cars(message.from_user.id)
    if cars:
        await message.answer(
            "Your cars 🚗 Choose one or add a new car:" if is_english(language_code) else "Ваши автомобили 🚗 Выберите или добавьте новый:",
            reply_markup=garage_keyboard(cars, language_code),
        )
    else:
        await message.answer(
            "Your garage is empty. Add your car!" if is_english(language_code) else "Гараж пока пустой. Добавьте свой автомобиль!",
            reply_markup=garage_keyboard([], language_code),
        )

@router.callback_query(F.data == "add_car")
async def add_car_callback(callback: CallbackQuery, state: FSMContext):
    language_code = user_language_code(callback.from_user)
    await state.set_state(UserFlow.adding_vin)
    await callback.message.answer(
        (
            "Enter your vehicle VIN 👇\n\n"
            "_17 characters, usually on the windshield or in documents_\n\n"
            "If you do not know VIN, press “I don't know VIN”"
        )
        if is_english(language_code)
        else "Введите VIN-код вашего автомобиля 👇\n\n_17 символов, находится на лобовом стекле или в документах_\n\nЕсли не знаете VIN — нажмите «Не знаю VIN»",
        parse_mode="Markdown",
        reply_markup=vin_skip_keyboard(language_code),
    )
    await callback.answer()

@router.callback_query(F.data.startswith("select_car_"))
async def select_car_callback(callback: CallbackQuery, state: FSMContext):
    language_code = user_language_code(callback.from_user)
    try:
        car_id = int(callback.data.split("_")[-1])
    except (TypeError, ValueError):
        await callback.answer("Could not select the vehicle." if is_english(language_code) else "Не удалось выбрать автомобиль.", show_alert=True)
        return

    cars = await get_cars(callback.from_user.id)
    car = next((c for c in cars if c[0] == car_id), None)

    if car:
        car_id, vin, brand, model, year = car
        details = await get_car_details(callback.from_user.id, car_id)
        vehicle = format_vehicle_profile(details) if details else f"{brand} {model} {year} (VIN: {vin})"
        await state.update_data(vehicle=vehicle, selected_car_id=car_id)
        await state.set_state(UserFlow.waiting_for_problem)
        await callback.message.answer(
            (f"Selected *{escape_markdown(vehicle)}* 🚗\n\nDescribe the problem 👇" if is_english(language_code) else f"Выбран *{escape_markdown(vehicle)}* 🚗\n\nОпишите проблему 👇"),
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(language_code),
        )
        await callback.answer()
    else:
        await callback.answer("Vehicle not found." if is_english(language_code) else "Автомобиль не найден.", show_alert=True)

@router.callback_query(F.data.startswith("delete_car_"))
async def delete_car_callback(callback: CallbackQuery):
    language_code = user_language_code(callback.from_user)
    try:
        car_id = int(callback.data.split("_")[-1])
    except (TypeError, ValueError):
        await callback.answer("Could not delete the vehicle." if is_english(language_code) else "Не удалось удалить автомобиль.", show_alert=True)
        return

    deleted = await delete_car(callback.from_user.id, car_id)
    cars = await get_cars(callback.from_user.id)
    await callback.message.edit_reply_markup(reply_markup=garage_keyboard(cars, language_code))
    await callback.answer(("Deleted!" if deleted else "Vehicle not found.") if is_english(language_code) else ("Удалено!" if deleted else "Автомобиль не найден."))

@router.callback_query(F.data.startswith("feedback:"))
async def response_feedback_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    contexts = data.get("feedback_contexts", {})
    message_id = str(callback.message.message_id) if callback.message else ""
    context = contexts.get(message_id)

    if not context:
        await callback.answer("Could not find the answer to rate." if is_english(user_language_code(callback.from_user)) else "Не нашёл ответ для оценки.", show_alert=True)
        return

    helpful = callback.data == "feedback:helpful"
    await save_response_feedback(
        user_id=callback.from_user.id,
        response_type=context["response_type"],
        problem=context["problem"],
        vehicle=context.get("vehicle", ""),
        helpful=helpful,
    )
    contexts.pop(message_id, None)
    await state.update_data(feedback_contexts=contexts)
    language_code = user_language_code(callback.from_user)
    await callback.answer("Thanks, saved." if is_english(language_code) else "Спасибо, запомнил.")
    if callback.message:
        await callback.message.edit_text(
            "Thanks for the rating. It helps me give more accurate answers."
            if is_english(language_code)
            else "Спасибо за оценку. Это помогает мне давать более точные ответы."
        )
