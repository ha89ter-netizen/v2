from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext

from states import UserFlow
from keyboards import (
    fix_choice_keyboard,
    diy_help_keyboard,
    success_keyboard,
    location_keyboard,
    main_menu_keyboard,
)
from services.openai_ai import (
    detect_intent,
    get_diy_instructions,
    get_diagnosis,
    continue_conversation,
)

router = Router()

def service_choice_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔧 СТО")],
            [KeyboardButton(text="🛞 Шиномонтаж")],
            [KeyboardButton(text="🔩 Запчасти")],
            [KeyboardButton(text="🔋 АКБ")],
            [KeyboardButton(text="⛽ Заправка")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

SERVICE_MAP = {
    "🔧 СТО": "sto",
    "🛞 Шиномонтаж": "tire",
    "🔩 Запчасти": "parts",
    "🔋 АКБ": "battery",
    "⛽ Заправка": "gas",
}

# Выбор типа сервиса
@router.message(F.text.in_(SERVICE_MAP.keys()))
async def handle_service_choice(message: Message, state: FSMContext):
    category = SERVICE_MAP[message.text]
    await state.update_data(forced_category=category)
    await state.set_state(UserFlow.waiting_for_location)
    await message.answer(
        "Отправьте геолокацию или введите адрес 👇",
        reply_markup=location_keyboard(),
    )

# Универсальный умный хендлер
@router.message(F.text)
async def smart_handler(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    current_state = await state.get_state()

    # Системные кнопки
    if text == "🏠 Главное меню":
        await state.clear()
        await state.set_state(UserFlow.main_menu)
        await message.answer("Главное меню 👇", reply_markup=main_menu_keyboard())
        return

    if text == "🔧 Новая проблема":
        await state.clear()
        await state.set_state(UserFlow.waiting_for_problem)
        await message.answer("Опишите проблему с автомобилем 👇")
        return

    if text == "✅ Починил!":
        await state.set_state(UserFlow.main_menu)
        await message.answer(
            "Отлично, рад что помог! 👍\n"
            "Если что-то ещё понадобится — обращайтесь.",
            reply_markup=success_keyboard(),
        )
        return

    if text == "❓ Не получается":
        await message.answer(
            "Не переживайте, бывает! Найти ближайший сервис?",
            reply_markup=fix_choice_keyboard(),
        )
        return

    # Определяем намерение
    intent = await detect_intent(text)

    # find_service — найти сервис
    if intent == "find_service" or text == "🏪 Найди сервис":
        await message.answer(
            "Какой сервис нужен? 👇",
            reply_markup=service_choice_keyboard(),
        )
        return

    # diy_repair — починить сам
    if intent == "diy_repair" or text == "🔧 Сам починю":
        problem = data.get("problem", text)
        vehicle = data.get("vehicle", "не указан")
        await message.answer("Готовлю инструкцию...")
        instructions = await get_diy_instructions(problem, vehicle)
        await state.update_data(history=[
            {"role": "user", "content": f"Авто: {vehicle}, проблема: {problem}"},
            {"role": "assistant", "content": instructions}
        ])
        await state.set_state(UserFlow.diy_mode)
        await message.answer(instructions, reply_markup=diy_help_keyboard())
        return

    # garage — открыть гараж
    if intent == "garage":
        from database import get_cars
        from keyboards import garage_keyboard
        await state.set_state(UserFlow.garage)
        cars = await get_cars(message.from_user.id)
        await message.answer(
            "Ваши автомобили 🚗" if cars else "Гараж пока пустой. Добавьте автомобиль!",
            reply_markup=garage_keyboard(cars),
        )
        return

    # location — обновить локацию
    if intent == "location":
        await state.set_state(UserFlow.waiting_for_location)
        await message.answer(
            "Отправьте геолокацию или введите адрес 👇",
            reply_markup=location_keyboard(),
        )
        return

    # diagnose — новая проблема
    if intent == "diagnose":
        await state.update_data(problem=text)
        await state.set_state(UserFlow.waiting_for_problem)
        from handlers.problem import receive_problem
        await receive_problem(message, state)
        return

    # question — продолжаем разговор
    problem = data.get("problem", "")
    vehicle = data.get("vehicle", "не указан")
    history = data.get("history", [])

    await message.bot.send_chat_action(message.chat.id, "typing")
    reply, updated_history = await continue_conversation(
        user_message=text,
        problem=problem,
        vehicle=vehicle,
        history=history,
    )
    await state.update_data(history=updated_history)
    await message.answer(reply, reply_markup=diy_help_keyboard())

