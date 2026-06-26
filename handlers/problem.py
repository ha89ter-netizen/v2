from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states import UserFlow
from keyboards import (
    vin_skip_keyboard,
    fix_choice_keyboard,
    diagnosis_parts_keyboard,
    urgent_help_keyboard,
    service_choice_keyboard,
    problem_onset_keyboard,
    main_menu_keyboard,
    diagnostic_details_keyboard,
)
from services.openai_ai import get_initial_advice, get_diagnosis
from services.feedback import ask_response_feedback
from services.deep_diagnostics import (
    diagnostic_questions_text,
    enrich_problem_context,
    needs_quick_clarification,
    quick_question_text,
)
from services.i18n import is_english, user_language_code
from services.safety import critical_warning, detect_safety_risk
from services.parts.parts_classifier import format_candidates, infer_part_candidates, should_offer_parts
from database import add_user, create_issue, update_issue

router = Router()

ONSET_LABELS = {
    "⚡ Внезапно": "появилась внезапно",
    "📈 Постепенно": "развивалась постепенно",
    "❔ Не знаю": "пользователь не уверен, когда началось",
    "⚡ Suddenly": "appeared suddenly",
    "📈 Gradually": "developed gradually",
    "❔ Not sure": "user is not sure when it started",
}


def _serialize_part_candidates(candidates):
    return [
        {
            "key": candidate.part.key,
            "name_ru": candidate.part.name_ru,
            "name_en": candidate.part.name_en,
            "confidence": candidate.confidence,
            "system": candidate.part.system,
        }
        for candidate in candidates
    ]


def _problem_with_onset(problem: str, onset: str, language_code: str = "", details: str = "") -> str:
    if not onset and not details:
        return problem
    return enrich_problem_context(problem, onset, details, language_code)


async def _run_problem_analysis(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    language_code = data.get("language_code") or user_language_code(message.from_user)
    problem = data.get("problem", "")
    onset = data.get("problem_onset", "")
    details = data.get("diagnostic_details", "")
    issue_id = data.get("issue_id")
    vehicle = data.get("vehicle", "")
    problem_for_ai = _problem_with_onset(problem, onset, language_code, details)

    if vehicle:
        await state.set_state(UserFlow.helping)
        await message.answer("Analyzing the problem for your vehicle..." if is_english(language_code) else "Анализирую проблему под ваш автомобиль...")
        diagnosis = await get_diagnosis(problem_for_ai, vehicle, language_code)
        await update_issue(
            issue_id=issue_id,
            user_id=message.from_user.id,
            diagnosis=diagnosis,
            status="diagnosed",
        )
        await message.answer(diagnosis, reply_markup=fix_choice_keyboard(language_code))
        candidates = infer_part_candidates(problem_for_ai, diagnosis)
        if should_offer_parts(candidates):
            await state.update_data(parts_candidates=_serialize_part_candidates(candidates))
            top = candidates[0]
            await message.answer(
                f"{format_candidates(candidates, language_code=language_code)}\n\n"
                + ("It looks like a part replacement may be needed. I can pick suitable options now." if is_english(language_code) else "Похоже, может понадобиться замена детали. Могу сразу подобрать варианты."),
                reply_markup=diagnosis_parts_keyboard(top.part.name_en if is_english(language_code) else top.part.name_ru, language_code),
            )
        await ask_response_feedback(
            message,
            state,
            "Was this diagnosis helpful?" if is_english(language_code) else "Диагноз был полезен?",
            "diagnosis",
            problem_for_ai,
            vehicle,
        )
    else:
        await message.answer("Analyzing the problem..." if is_english(language_code) else "Анализирую проблему...")
        advice = await get_initial_advice(problem_for_ai, language_code)
        await update_issue(
            issue_id=issue_id,
            user_id=message.from_user.id,
            initial_advice=advice,
            status="initial_advice",
        )
        extra = (
            "For a more precise answer for your exact model, add a car to the garage "
            "or send VIN / make, model, and year."
            if is_english(language_code)
            else "Для более точного совета под вашу модель добавьте авто в гараж или напишите VIN / марку, модель и год."
        )
        await message.answer(f"{advice}\n\n{extra}", reply_markup=fix_choice_keyboard(language_code))
        await ask_response_feedback(
            message,
            state,
            "Was this general advice helpful?" if is_english(language_code) else "Этот общий совет был полезен?",
            "initial_advice",
            problem_for_ai,
        )
        await state.set_state(UserFlow.waiting_for_vehicle)
        prompt = (
            "Want to add the vehicle now? Enter VIN or make, model, and year 👇\n\n"
            "_Example: Toyota Camry 2019. If you do not know VIN, press the skip button._"
            if is_english(language_code)
            else "Уточнить автомобиль сейчас? Введите VIN или марку, модель и год 👇\n\n_Например: Toyota Camry 2019. Если не хотите — нажмите «Не знаю VIN»._"
        )
        await message.answer(prompt, parse_mode="Markdown", reply_markup=vin_skip_keyboard(language_code))

@router.message(F.text.in_({"🔧 Диагностика", "🔧 Описать проблему", "🔧 Describe problem"}))
async def btn_describe_problem(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    await state.set_state(UserFlow.waiting_for_problem)
    await state.update_data(language_code=language_code)
    await message.answer("Describe the car problem in your own words 👇" if is_english(language_code) else "Опишите проблему с автомобилем своими словами 👇")

@router.message(F.text.in_({"📍 Сервис рядом", "📍 Найти сервис рядом", "📍 Find service nearby"}))
async def btn_find_service(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    await state.update_data(problem="nearby service search" if is_english(language_code) else "поиск ближайшего сервиса", language_code=language_code)
    await state.set_state(UserFlow.helping)
    await message.answer(
        "What type of service do you need? 👇" if is_english(language_code) else "Какой сервис нужен? 👇",
        reply_markup=service_choice_keyboard(language_code),
    )

@router.message(F.text.in_({"🚨 Срочная помощь", "🚨 Emergency help"}))
async def btn_emergency_help(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    await state.update_data(
        problem="urgent roadside help" if is_english(language_code) else "срочная помощь на дороге",
        forced_category="tow",
        risk_level="critical",
        language_code=language_code,
    )
    await state.set_state(UserFlow.waiting_for_location)
    from keyboards import location_keyboard
    await message.answer(
        "Got it. I will find urgent help nearby. Send your location or address 👇" if is_english(language_code) else "Понял. Найдём срочную помощь рядом. Отправьте геолокацию или адрес 👇",
        reply_markup=location_keyboard(language_code),
    )

@router.message(UserFlow.waiting_for_problem, F.text)
async def receive_problem(message: Message, state: FSMContext):
    problem = message.text.strip()
    language_code = user_language_code(message.from_user)

    if len(problem) < 5:
        await message.answer("Please describe the problem in a bit more detail 🙏" if is_english(language_code) else "Пожалуйста опишите проблему подробнее 🙏")
        return

    safety = detect_safety_risk(problem)
    data = await state.get_data()
    vehicle = data.get("vehicle", "")
    selected_car_id = data.get("selected_car_id")
    await add_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.language_code or "ru",
    )
    issue_id = await create_issue(
        user_id=message.from_user.id,
        problem=problem,
        vehicle=vehicle,
        car_id=selected_car_id,
        risk_level=safety["risk_level"],
        status="safety_escalated" if safety["risk_level"] == "critical" else "new",
    )
    await state.update_data(
        problem=problem,
        issue_id=issue_id,
        risk_level=safety["risk_level"],
        language_code=language_code,
    )

    if safety["risk_level"] == "critical":
        await state.set_state(UserFlow.helping)
        await message.answer(critical_warning(language_code), reply_markup=urgent_help_keyboard(language_code))
        return

    await state.set_state(UserFlow.waiting_for_problem_onset)
    await message.answer(
        "Did the problem appear suddenly or gradually?" if is_english(language_code) else "Проблема появилась внезапно или постепенно?",
        reply_markup=problem_onset_keyboard(language_code),
    )


@router.message(UserFlow.waiting_for_problem_onset, F.text)
async def receive_problem_onset(message: Message, state: FSMContext):
    text = message.text.strip()
    language_code = user_language_code(message.from_user)
    if text in {"🏠 Главное меню", "🏠 Main menu"}:
        await state.clear()
        await state.set_state(UserFlow.main_menu)
        await message.answer("Main menu 👇" if is_english(language_code) else "Главное меню 👇", reply_markup=main_menu_keyboard(language_code))
        return

    onset = ONSET_LABELS.get(text, text)
    if len(onset) < 2:
        await message.answer("Choose an option with a button or write a short answer." if is_english(language_code) else "Выберите вариант кнопкой или напишите коротко.")
        return

    await state.update_data(problem_onset=onset)
    data = await state.get_data()
    problem = data.get("problem", "")
    if not needs_quick_clarification(problem):
        await state.update_data(diagnostic_details="")
        await _run_problem_analysis(message, state)
        return

    await state.set_state(UserFlow.waiting_for_diagnostic_details)
    await state.update_data(diagnostic_details_mode="quick")
    await message.answer(
        quick_question_text(problem, language_code),
        reply_markup=diagnostic_details_keyboard(language_code),
    )


@router.message(UserFlow.waiting_for_diagnostic_details, F.text)
async def receive_diagnostic_details(message: Message, state: FSMContext):
    text = message.text.strip()
    language_code = user_language_code(message.from_user)
    if text in {"🏠 Главное меню", "🏠 Main menu"}:
        await state.clear()
        await state.set_state(UserFlow.main_menu)
        await message.answer("Main menu 👇" if is_english(language_code) else "Главное меню 👇", reply_markup=main_menu_keyboard(language_code))
        return

    details = "" if text in {"⏭ Пропустить уточнение", "⏭ Skip details"} else text
    if details and len(details) < 3:
        await message.answer(
            "Write a bit more detail or press “Skip details”." if is_english(language_code) else "Напишите чуть подробнее или нажмите «Пропустить уточнение».",
            reply_markup=diagnostic_details_keyboard(language_code),
        )
        return

    await state.update_data(diagnostic_details=details)
    await _run_problem_analysis(message, state)


@router.message(F.text.in_({"🔍 Глубже разобрать", "🔍 Analyze deeper"}))
async def btn_analyze_deeper(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    data = await state.get_data()
    problem = data.get("problem", "")
    if not problem:
        await state.set_state(UserFlow.waiting_for_problem)
        await message.answer(
            "First describe the car problem 👇" if is_english(language_code) else "Сначала опишите проблему с автомобилем 👇"
        )
        return

    await state.set_state(UserFlow.waiting_for_diagnostic_details)
    await state.update_data(diagnostic_details_mode="deep")
    await message.answer(
        diagnostic_questions_text(problem, language_code),
        reply_markup=diagnostic_details_keyboard(language_code),
    )
