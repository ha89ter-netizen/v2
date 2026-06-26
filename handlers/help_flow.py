from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states import UserFlow
from keyboards import (
    fix_choice_keyboard,
    diy_help_keyboard,
    diy_troubleshoot_keyboard,
    success_keyboard,
    location_keyboard,
    main_menu_keyboard,
    service_choice_keyboard,
    urgent_help_keyboard,
    vin_skip_keyboard,
)
from services.feedback import ask_response_feedback
from services.openai_ai import (
    detect_intent,
    get_diy_instructions,
    get_diagnosis,
    continue_conversation,
)
from database import update_issue
from services.i18n import is_english, user_language_code
from services.safety import critical_warning
from services.service_categories import SERVICE_BUTTON_TO_CATEGORY

router = Router()

def _drive_safety_answer(data: dict, language_code: str = "") -> str:
    problem = (data.get("problem") or "").lower()
    risk_level = data.get("risk_level", "normal")
    danger_words = (
        "тормоз", "руль", "дым", "масло горит", "температура", "перегрев",
        "течь топлива", "бензин течет", "заглох", "не завод", "колесо болтается",
    )
    caution_words = (
        "стук", "скрип", "вибрация", "трясет", "дергается", "чек", "ошибка",
    )

    if risk_level == "critical" or any(word in problem for word in danger_words):
        if is_english(language_code):
            return (
                "It is better not to drive.\n\n"
                "Stop in a safe place, turn on hazard lights, and call a tow truck or urgent help. "
                "If the issue involves brakes, steering, overheating, smoke, or fuel leak, driving is dangerous."
            )
        return (
            "Лучше не ехать своим ходом.\n\n"
            "Остановитесь в безопасном месте, включите аварийку и вызывайте эвакуатор "
            "или срочную помощь. Если проблема связана с тормозами, рулём, перегревом, "
            "дымом или течью топлива, продолжать движение опасно."
        )
    if any(word in problem for word in caution_words):
        if is_english(language_code):
            return (
                "You may drive only carefully and for a short distance if there is no smoke, fuel smell, "
                "overheating, brake loss, or strong steering pull.\n\n"
                "The best option is to go slowly to the nearest diagnostics and avoid highways."
            )
        return (
            "Ехать можно только осторожно и недалеко, если нет дыма, запаха топлива, "
            "перегрева, потери тормозов или сильного увода руля.\n\n"
            "Лучший вариант — доехать до ближайшей диагностики без резких ускорений "
            "и не выезжать на трассу."
        )
    if is_english(language_code):
        return (
            "Your description has no obvious critical sign, but that is not a safety guarantee.\n\n"
            "If the car brakes, steers, and temperature stays normal, you can carefully drive to a service. "
            "If the symptom gets worse, stop and find help nearby."
        )
    return (
        "По описанию нет явного критического признака, но это не гарантия безопасности.\n\n"
        "Если машина тормозит, рулится и не перегревается нормально — можно аккуратно "
        "доехать до сервиса. Если симптом усиливается, лучше остановиться и искать помощь рядом."
    )

# Выбор типа сервиса
@router.message(F.text.in_(SERVICE_BUTTON_TO_CATEGORY.keys()))
async def handle_service_choice(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    category = SERVICE_BUTTON_TO_CATEGORY[message.text]
    await state.update_data(forced_category=category, language_code=language_code)
    await state.set_state(UserFlow.waiting_for_location)
    await message.answer(
        "Send your location or enter an address 👇" if is_english(language_code) else "Отправьте геолокацию или введите адрес 👇",
        reply_markup=location_keyboard(language_code),
    )

# Универсальный умный хендлер
@router.message(F.text)
async def smart_handler(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    language_code = data.get("language_code") or user_language_code(message.from_user)
    english = is_english(language_code)

    # Системные кнопки
    if text in {"🏠 Главное меню", "🏠 Main menu"}:
        await state.clear()
        await state.set_state(UserFlow.main_menu)
        await message.answer("Main menu 👇" if english else "Главное меню 👇", reply_markup=main_menu_keyboard(language_code))
        return

    if text in {"🔧 Новая проблема", "🔧 New problem"}:
        await state.clear()
        await state.set_state(UserFlow.waiting_for_problem)
        await state.update_data(language_code=language_code)
        await message.answer("Describe the car problem 👇" if english else "Опишите проблему с автомобилем 👇")
        return

    if text in {"🔍 Уточнить по авто", "🔍 Add vehicle"}:
        problem = data.get("problem", "")
        if not problem:
            await state.set_state(UserFlow.waiting_for_problem)
            await message.answer("Describe the problem, then I will tailor the diagnosis to your vehicle 👇" if english else "Опишите проблему, и я уточню диагноз по автомобилю 👇")
            return
        await state.set_state(UserFlow.waiting_for_vehicle)
        await message.answer(
            "Enter VIN or make, model, and year 👇" if english else "Введите VIN-код или марку, модель и год автомобиля 👇",
            reply_markup=vin_skip_keyboard(language_code),
        )
        return

    if text in {"🔍 Уточнить по фото", "🔍 Clarify photo"}:
        await message.answer(
            "Write what you want to clarify from the photo: when it appeared, whether there is sound, smell, leak, or dashboard warning."
            if english
            else "Напишите, что именно хотите уточнить по фото: когда появилось, есть ли звук, запах, течь или ошибка на панели."
        )
        return

    if text in {"📜 Сохранить в историю", "📜 Save to history"}:
        await message.answer("Already saved to history. Open it with the “📜 History” button." if english else "Уже сохранено в историю. Открыть историю можно кнопкой «📜 История».")
        return

    if text in {"📜 Сохранить ремонт в историю", "📜 Save repair to history"}:
        issue_id = data.get("issue_id")
        if issue_id:
            await update_issue(issue_id, message.from_user.id, status="diy_saved")
        await message.answer("Saved the repair to history. Open it with “📜 History”." if english else "Сохранил ремонт в историю. Открыть её можно кнопкой «📜 История».")
        return

    if text in {"🚦 Можно ли ехать?", "🚦 Can I drive?"}:
        await message.answer(_drive_safety_answer(data, language_code), reply_markup=urgent_help_keyboard(language_code))
        return

    if text in {"🧭 Продолжить ремонт", "🧭 Continue repair"}:
        await state.update_data(awaiting_diy_troubleshoot=True)
        await message.answer(
            (
                "Write which step stopped you and what exactly did not work. "
                "I will give the next step instead of repeating the whole instruction."
            )
            if english
            else (
                "Напишите, на каком шаге остановились и что именно не получилось. "
                "Я дам следующий шаг, а не буду повторять инструкцию сначала."
            ),
            reply_markup=diy_troubleshoot_keyboard(language_code),
        )
        return

    if text in {"🚨 Срочная помощь", "🚨 Эвакуатор / срочная помощь", "🚨 Emergency help", "🚨 Tow truck / urgent help"}:
        issue_id = data.get("issue_id")
        if issue_id:
            await update_issue(issue_id, message.from_user.id, status="searching_service")
        await state.update_data(forced_category="tow", problem=data.get("problem", "urgent roadside help" if english else "срочная помощь на дороге"))
        await state.set_state(UserFlow.waiting_for_location)
        await message.answer(
            "I will find urgent help nearby. Send your location or address 👇" if english else "Найдём срочную помощь рядом. Отправьте геолокацию или адрес 👇",
            reply_markup=location_keyboard(language_code),
        )
        return

    if text in {"🔩 Магазин запчастей рядом", "🔩 Parts store nearby"}:
        await state.update_data(forced_category="parts", problem=data.get("problem", "parts store"))
        await state.set_state(UserFlow.waiting_for_location)
        await message.answer(
            "I will find a parts store nearby. Send your location or address 👇" if english else "Найдём магазин запчастей рядом. Отправьте геолокацию или адрес 👇",
            reply_markup=location_keyboard(language_code),
        )
        return

    if text in {"✅ Починил!", "✅ Fixed it"}:
        issue_id = data.get("issue_id")
        if issue_id:
            await update_issue(issue_id, message.from_user.id, status="fixed")
        await state.set_state(UserFlow.main_menu)
        await message.answer(
            "Great, glad I helped! 👍\nIf you need anything else, I am here."
            if english
            else "Отлично, рад что помог! 👍\nЕсли что-то ещё понадобится — обращайтесь.",
            reply_markup=success_keyboard(language_code),
        )
        return

    if text in {"❓ Не получается", "❓ It did not work"}:
        issue_id = data.get("issue_id")
        if issue_id:
            await update_issue(issue_id, message.from_user.id, status="diy_stuck")
        await state.update_data(awaiting_diy_troubleshoot=True)
        await message.answer(
            "Okay, we will not drop it. Write what exactly did not work: which step, what you see/hear, any error, or what will not come loose."
            if english
            else "Ок, не бросаем. Напишите, что именно не получилось: какой шаг, что видите/слышите, какая ошибка или что не откручивается.",
            reply_markup=diy_troubleshoot_keyboard(language_code),
        )
        return

    if data.get("awaiting_diy_troubleshoot") and text not in {"🏪 Найди сервис", "🏪 Find service"}:
        problem = data.get("problem", "")
        vehicle = data.get("vehicle", "не указан")
        history = data.get("history", [])

        await message.bot.send_chat_action(message.chat.id, "typing")
        reply, updated_history = await continue_conversation(
            user_message=(
                (
                    "The user could not complete the DIY instruction. Do not repeat the whole instruction. "
                    "Give the next practical step, a check option, and when to stop and go to a service.\n\n"
                    f"What did not work: {text}"
                )
                if english
                else (
                    "У пользователя не получилось выполнить DIY-инструкцию. "
                    "Не повторяй всю инструкцию сначала. Дай следующий практический шаг, "
                    "вариант проверки и когда лучше остановиться и ехать в сервис.\n\n"
                    f"Что не получилось: {text}"
                )
            ),
            problem=problem,
            vehicle=vehicle,
            history=history,
            language_code=language_code,
        )
        await state.update_data(history=updated_history, awaiting_diy_troubleshoot=True)
        await message.answer(reply, reply_markup=diy_troubleshoot_keyboard(language_code))
        return

    # Определяем намерение
    intent = await detect_intent(text)

    # find_service — найти сервис
    if intent == "find_service" or text in {"🏪 Найди сервис", "🏪 Find service"}:
        issue_id = data.get("issue_id")
        if issue_id:
            await update_issue(issue_id, message.from_user.id, status="searching_service")
        await message.answer(
            "What type of service do you need? 👇" if english else "Какой сервис нужен? 👇",
            reply_markup=service_choice_keyboard(language_code),
        )
        return

    # diy_repair — починить сам
    if intent == "diy_repair" or text in {"🔧 Сам починю", "🔧 Что сделать самому", "🔧 I'll fix it", "🔧 What can I do myself"}:
        problem = data.get("problem", text)
        vehicle = data.get("vehicle", "не указан")
        if data.get("risk_level") == "critical":
            issue_id = data.get("issue_id")
            if issue_id:
                await update_issue(issue_id, message.from_user.id, status="diy_blocked")
            await message.answer(critical_warning(language_code), reply_markup=urgent_help_keyboard(language_code))
            return

        issue_id = data.get("issue_id")
        if issue_id:
            await update_issue(issue_id, message.from_user.id, status="diy")
        await message.answer("Preparing instructions..." if english else "Готовлю инструкцию...")
        instructions = await get_diy_instructions(problem, vehicle, language_code)
        await state.update_data(history=[
            {"role": "user", "content": f"Vehicle: {vehicle}, problem: {problem}" if english else f"Авто: {vehicle}, проблема: {problem}"},
            {"role": "assistant", "content": instructions}
        ])
        await state.set_state(UserFlow.diy_mode)
        await message.answer(instructions, reply_markup=diy_help_keyboard(language_code))
        await ask_response_feedback(
            message,
            state,
            "Were these instructions helpful?" if english else "Инструкция была полезна?",
            "diy_instructions",
            problem,
            vehicle,
        )
        return

    # garage — открыть гараж
    if intent == "garage":
        from database import get_cars
        from keyboards import garage_keyboard
        await state.set_state(UserFlow.garage)
        cars = await get_cars(message.from_user.id)
        await message.answer(
            ("Your cars 🚗" if cars else "Your garage is empty. Add a car!")
            if english
            else ("Ваши автомобили 🚗" if cars else "Гараж пока пустой. Добавьте автомобиль!"),
            reply_markup=garage_keyboard(cars, language_code),
        )
        return

    # location — обновить локацию
    if intent == "location":
        await state.set_state(UserFlow.waiting_for_location)
        await message.answer(
            "Send your location or enter an address 👇" if english else "Отправьте геолокацию или введите адрес 👇",
            reply_markup=location_keyboard(language_code),
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
        language_code=language_code,
    )
    await state.update_data(history=updated_history)
    await message.answer(reply, reply_markup=diy_help_keyboard(language_code))
