import logging
from typing import Optional

from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database import get_car_details, update_issue
from keyboards import (
    main_menu_keyboard,
    parts_after_result_keyboard,
    parts_budget_keyboard,
    vin_skip_keyboard,
)
from services.parts.budget_filter import choose_recommendation, parse_budget
from services.parts.oem_lookup import lookup_parts
from services.parts.parts_classifier import classify_part_request
from services.parts.parts_response_builder import build_parts_response
from services.parts.vin_parts_service import (
    VehicleContext,
    vehicle_from_car_row,
    vehicle_from_text,
)
from services.i18n import is_english, user_language_code
from services.vin_decoder import clean_vin, decode_vin
from states import UserFlow

logger = logging.getLogger(__name__)

router = Router()


def _candidate_from_state(data: dict):
    candidates = data.get("parts_candidates") or []
    if not candidates:
        return None
    top = candidates[0]
    return top if isinstance(top, dict) else None


async def _resolve_vehicle(message: Message, state: FSMContext) -> Optional[VehicleContext]:
    data = await state.get_data()
    selected_car_id = data.get("selected_car_id")
    if selected_car_id:
        row = await get_car_details(message.from_user.id, selected_car_id)
        vehicle = vehicle_from_car_row(row)
        if vehicle:
            return vehicle

    vehicle_text = data.get("vehicle", "")
    if vehicle_text:
        return vehicle_from_text(vehicle_text)
    return None


async def _ask_vehicle(message: Message, state: FSMContext) -> None:
    language_code = user_language_code(message.from_user)
    await state.set_state(UserFlow.waiting_for_part_vehicle)
    await message.answer(
        (
            "To match the part accurately, I need the vehicle.\n\n"
            "Enter VIN or make, model, and year. Example:\n"
            "`Toyota Sequoia 2018`"
        )
        if is_english(language_code)
        else (
            "Чтобы подобрать деталь точнее, нужен автомобиль.\n\n"
            "Введите VIN или марку, модель и год. Например:\n"
            "`Toyota Sequoia 2018`"
        ),
        parse_mode="Markdown",
        reply_markup=vin_skip_keyboard(language_code),
    )


async def _ask_part_name(message: Message, state: FSMContext) -> None:
    language_code = user_language_code(message.from_user)
    await state.set_state(UserFlow.waiting_for_part_name)
    await message.answer(
        (
            "Which part are we looking for? 👇\n\n"
            "Examples: ignition coil, brake pads, shock absorber, spark plug, headlight, fuel pump."
        )
        if is_english(language_code)
        else "Какую деталь ищем? 👇\n\nНапример: катушка зажигания, тормозные колодки, амортизатор, свеча, фара, бензонасос."
    )


async def _ask_budget(message: Message, state: FSMContext, part_name: str) -> None:
    language_code = user_language_code(message.from_user)
    await state.set_state(UserFlow.waiting_for_part_budget)
    await message.answer(
        f"Got it, searching for: {part_name}.\n\nChoose a budget:" if is_english(language_code) else f"Понял, ищем: {part_name}.\n\nВыберите бюджет:",
        reply_markup=parts_budget_keyboard(language_code),
    )


async def _start_parts_flow(message: Message, state: FSMContext, part_text: str = "") -> None:
    language_code = user_language_code(message.from_user)
    await state.update_data(language_code=language_code)
    vehicle = await _resolve_vehicle(message, state)
    if not vehicle:
        if part_text:
            candidate = classify_part_request(part_text)
            await state.update_data(part_key=candidate.part.key, part_name=candidate.part.name_en if is_english(language_code) else candidate.part.name_ru)
        await _ask_vehicle(message, state)
        return

    data = await state.get_data()
    if not part_text:
        stored = _candidate_from_state(data)
        if stored:
            part_text = stored.get("name_en" if is_english(language_code) else "name_ru", "")
            await state.update_data(part_key=stored.get("key"), part_name=part_text)

    if not part_text and data.get("part_name"):
        part_text = data["part_name"]

    if not part_text:
        await _ask_part_name(message, state)
        return

    candidate = classify_part_request(part_text)
    await state.update_data(
        vehicle=vehicle.display_name,
        part_key=candidate.part.key,
        part_name=candidate.part.name_en if is_english(language_code) else candidate.part.name_ru,
        part_confidence=candidate.confidence,
    )
    await _ask_budget(message, state, candidate.part.name_en if is_english(language_code) else candidate.part.name_ru)


@router.message(F.text.in_({"🔩 Найти запчасть", "🔩 Найти другую запчасть", "🔩 Find part", "🔩 Find another part"}))
async def btn_find_part(message: Message, state: FSMContext):
    await state.update_data(part_key=None, part_name=None)
    await _start_parts_flow(message, state)


@router.message(F.text.startswith("🔩 Найти "))
async def btn_find_specific_part(message: Message, state: FSMContext):
    text = message.text.replace("🔩 Найти", "", 1).strip()
    if text == "подходящую запчасть":
        text = ""
    await _start_parts_flow(message, state, text)


@router.message(F.text.startswith("🔩 Find "))
async def btn_find_specific_part_en(message: Message, state: FSMContext):
    text = message.text.replace("🔩 Find", "", 1).strip()
    if text == "suitable part":
        text = ""
    await _start_parts_flow(message, state, text)


@router.message(F.text.in_({"🔩 Найти подходящую запчасть", "🔩 Find suitable part"}))
async def btn_find_likely_part(message: Message, state: FSMContext):
    await _start_parts_flow(message, state)


@router.message(F.text.in_({"🔧 Продолжить диагностику", "🔧 Continue diagnosis"}))
async def continue_diagnosis_from_parts(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    await state.set_state(UserFlow.helping)
    await message.answer("Continuing diagnosis. Write what you want to clarify." if is_english(language_code) else "Продолжаем диагностику. Напишите, что хотите уточнить.", reply_markup=main_menu_keyboard(language_code))


@router.message(UserFlow.waiting_for_part_vehicle, F.text)
async def receive_part_vehicle(message: Message, state: FSMContext):
    text = message.text.strip()
    language_code = user_language_code(message.from_user)
    if text in {"⏭ Не знаю VIN", "⏭ I don't know VIN"}:
        await message.answer("Then write make, model, and year. Example: Toyota Camry 2019" if is_english(language_code) else "Тогда напишите марку, модель и год автомобиля. Например: Toyota Camry 2019")
        return
    if len(text) < 3:
        await message.answer("Write the vehicle in more detail." if is_english(language_code) else "Напишите автомобиль подробнее.")
        return

    clean = clean_vin(text)
    if clean:
        await message.answer("Identifying the vehicle by VIN..." if is_english(language_code) else "Определяю автомобиль по VIN...")
        vin_info = await decode_vin(clean)
        if not vin_info:
            await message.answer(
                "VIN accepted, but I could not identify the model.\nWrite make, model, and year manually for accurate matching."
                if is_english(language_code)
                else "VIN принят, но модель определить не удалось.\nНапишите марку, модель и год автомобиля вручную для точного подбора."
            )
            return

        brand = vin_info.get("manufacturer", "")
        model = vin_info.get("model", "")
        year = str(vin_info.get("year", ""))
        vehicle_label = " ".join(part for part in [brand, model, year] if part).strip()
        vehicle_label = f"{vehicle_label} (VIN: {clean})" if vehicle_label else f"VIN: {clean}"
        await message.answer(f"VIN identified: {vehicle_label}" if is_english(language_code) else f"VIN определён: {vehicle_label}")
    else:
        vehicle = vehicle_from_text(text)
        vehicle_label = vehicle.display_name or text

    await state.update_data(vehicle=vehicle_label, selected_car_id=None)
    data = await state.get_data()
    if data.get("part_name"):
        await _ask_budget(message, state, data["part_name"])
    else:
        await _ask_part_name(message, state)


@router.message(UserFlow.waiting_for_part_name, F.text)
async def receive_part_name(message: Message, state: FSMContext):
    text = message.text.strip()
    language_code = user_language_code(message.from_user)
    if len(text) < 2:
        await message.answer("Write the part name in a bit more detail." if is_english(language_code) else "Напишите название детали чуть подробнее.")
        return
    candidate = classify_part_request(text)
    await state.update_data(
        part_key=candidate.part.key,
        part_name=candidate.part.name_en if is_english(language_code) else candidate.part.name_ru,
        part_confidence=candidate.confidence,
    )
    await _ask_budget(message, state, candidate.part.name_en if is_english(language_code) else candidate.part.name_ru)


@router.message(UserFlow.waiting_for_part_budget, F.text)
async def receive_part_budget(message: Message, state: FSMContext):
    data = await state.get_data()
    language_code = data.get("language_code") or user_language_code(message.from_user)
    budget = parse_budget(message.text)
    valid_budgets = {"до 20 000 ₸", "до 50 000 ₸", "до 100 000 ₸", "без ограничений", "up to 20 000 ₸", "up to 50 000 ₸", "up to 100 000 ₸", "no limit"}
    if message.text.strip().lower() not in valid_budgets:
        await message.answer("Choose a budget with a button 👇" if is_english(language_code) else "Выберите бюджет кнопкой 👇", reply_markup=parts_budget_keyboard(language_code))
        return

    vehicle = await _resolve_vehicle(message, state)
    if not vehicle:
        await _ask_vehicle(message, state)
        return

    part_key = data.get("part_key") or "unknown"
    candidate = classify_part_request(data.get("part_name", part_key))
    try:
        options = await lookup_parts(vehicle, part_key)
        recommendation = choose_recommendation(options, candidate.part, budget)
        await state.update_data(
            part_budget=message.text,
            part_last_result=recommendation.recommended.part_number,
        )
        issue_id = data.get("issue_id")
        if issue_id:
            await update_issue(issue_id, message.from_user.id, status="parts_selected")
        await state.set_state(UserFlow.helping)
        await message.answer(
            build_parts_response(vehicle, recommendation, language_code),
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=parts_after_result_keyboard(language_code),
        )
    except Exception as exc:
        logger.exception("Parts lookup failed: %s", exc)
        await message.answer(
            "Could not match the part from the mock catalog. Try another part name."
            if is_english(language_code)
            else "Не смог подобрать запчасть из mock-каталога. Попробуйте другое название детали.",
            reply_markup=parts_after_result_keyboard(language_code),
        )
