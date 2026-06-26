from io import BytesIO

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states import UserFlow
from keyboards import (
    fix_choice_keyboard,
    photo_context_keyboard,
    photo_action_keyboard,
    remove_keyboard,
    urgent_help_keyboard,
)
from database import add_user, create_issue, update_issue
from services.openai_ai import analyze_photo
from services.feedback import ask_response_feedback
from services.i18n import is_english, user_language_code
from services.safety import detect_safety_risk


router = Router()

PHOTO_PROMPT = (
    "Что на фото? Выберите тип снимка, потом отправьте фото 👇"
)
PHOTO_PROMPT_EN = "What is in the photo? Choose the photo type, then send the image 👇"

PHOTO_CONTEXTS = {
    "⚠️ Ошибка на панели",
    "🛞 Колесо или шина",
    "💧 Течь или жидкость",
    "🔧 Деталь под капотом",
    "🚗 Кузов или повреждение",
    "📷 Другое фото",
    "⚠️ Dashboard warning",
    "🛞 Wheel or tire",
    "💧 Leak or fluid",
    "🔧 Under-hood part",
    "🚗 Body damage",
    "📷 Other photo",
}


async def _start_photo_flow(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    await state.update_data(language_code=language_code)
    await state.set_state(UserFlow.waiting_for_photo_context)
    await message.answer(PHOTO_PROMPT_EN if is_english(language_code) else PHOTO_PROMPT, reply_markup=photo_context_keyboard(language_code))


@router.message(Command("photo"))
async def cmd_photo(message: Message, state: FSMContext):
    await _start_photo_flow(message, state)


@router.message(F.text.in_({"📷 Фото", "📷 Анализ фото", "📷 Photo"}))
async def btn_photo(message: Message, state: FSMContext):
    await _start_photo_flow(message, state)


@router.message(UserFlow.waiting_for_photo_context, F.text.in_(PHOTO_CONTEXTS))
async def receive_photo_context(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    await state.update_data(photo_context=message.text)
    await state.set_state(UserFlow.waiting_for_photo)
    await message.answer(
        "Now send the photo. You can add a caption: what happened, when it appeared, whether there is smell or sound."
        if is_english(language_code)
        else "Теперь отправьте фото. Можно добавить подпись: что произошло, когда появилось, есть ли запах/звук.",
        reply_markup=remove_keyboard(),
    )


@router.message(UserFlow.waiting_for_photo_context, F.text)
async def receive_unknown_photo_context(message: Message):
    language_code = user_language_code(message.from_user)
    await message.answer("Choose the photo type with a button below or send the image right away." if is_english(language_code) else "Выберите тип фото кнопкой ниже или сразу отправьте снимок.")


@router.message(UserFlow.waiting_for_photo_context, F.photo)
@router.message(UserFlow.waiting_for_photo, F.photo)
async def receive_photo(message: Message, state: FSMContext):
    await add_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.language_code or "ru",
    )

    caption = message.caption or ""
    data = await state.get_data()
    language_code = data.get("language_code") or user_language_code(message.from_user)
    vehicle = data.get("vehicle", "")
    selected_car_id = data.get("selected_car_id")
    photo_context = data.get("photo_context", "")
    problem_parts = ["Photo diagnostics" if is_english(language_code) else "Фото диагностика"]
    if photo_context:
        problem_parts.append(photo_context)
    if caption:
        problem_parts.append(caption)
    problem = ": ".join(problem_parts)

    issue_id = await create_issue(
        user_id=message.from_user.id,
        problem=problem,
        vehicle=vehicle,
        car_id=selected_car_id,
        status="photo_received",
    )
    await state.update_data(issue_id=issue_id, problem=problem)

    await message.answer("Analyzing the photo..." if is_english(language_code) else "Анализирую фото...")

    photo = message.photo[-1]
    buffer = BytesIO()
    await message.bot.download(photo.file_id, destination=buffer)

    analysis = await analyze_photo(
        buffer.getvalue(),
        caption=caption,
        photo_context=photo_context,
        language_code=language_code,
    )
    safety = detect_safety_risk(f"{photo_context} {caption} {analysis}")
    await update_issue(
        issue_id=issue_id,
        user_id=message.from_user.id,
        diagnosis=analysis,
        risk_level=safety["risk_level"],
        status="safety_escalated" if safety["risk_level"] == "critical" else "photo_analyzed",
    )

    await state.set_state(UserFlow.helping)
    await state.update_data(risk_level=safety["risk_level"])
    reply_markup = urgent_help_keyboard(language_code) if safety["risk_level"] == "critical" else photo_action_keyboard(language_code)
    await message.answer(analysis, reply_markup=reply_markup)
    await ask_response_feedback(
        message,
        state,
        "Was the photo analysis helpful?" if is_english(language_code) else "Анализ фото был полезен?",
        "photo_analysis",
        problem,
        vehicle,
    )


@router.message(UserFlow.waiting_for_photo)
async def receive_not_photo(message: Message):
    language_code = user_language_code(message.from_user)
    await message.answer("Please send an actual photo. You can add a caption to it." if is_english(language_code) else "Нужно отправить именно фото. Можно добавить подпись к снимку.")
