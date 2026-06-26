from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from typing import Optional

from states import UserFlow
from keyboards import fix_choice_keyboard, garage_keyboard
from services.feedback import ask_response_feedback
from services.openai_ai import get_diagnosis
from services.i18n import is_english, user_language_code
from database import add_car, get_cars, update_issue
from services.vin_decoder import clean_vin, decode_vin
from services.vehicle_profile import parse_vehicle_profile
from utils import escape_markdown

router = Router()

async def _save_car_from_vin(message: Message, vin: str) -> Optional[str]:
    language_code = user_language_code(message.from_user)
    vin_info = await decode_vin(vin)
    if not vin_info:
        return None

    brand = vin_info.get("manufacturer", "")
    model = vin_info.get("model", "")
    year = vin_info.get("year", "")
    await add_car(
        user_id=message.from_user.id,
        vin=vin,
        brand=brand,
        model=model,
        year=str(year),
    )
    await message.answer(
        (
            "Vehicle identified and saved:\n"
            f"Make: *{escape_markdown(brand)}*\n"
            f"Model: *{escape_markdown(model)}*\n"
            f"Year: *{escape_markdown(year)}*\n"
            f"VIN: `{escape_markdown(vin)}`"
        )
        if is_english(language_code)
        else (
            "Автомобиль определён и сохранён:\n"
            f"Марка: *{escape_markdown(brand)}*\n"
            f"Модель: *{escape_markdown(model)}*\n"
            f"Год: *{escape_markdown(year)}*\n"
            f"VIN: `{escape_markdown(vin)}`"
        ),
        parse_mode="Markdown",
    )
    return f"{brand} {model} {year} (VIN: {vin})"

async def _show_garage(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    await state.set_state(UserFlow.garage)
    cars = await get_cars(message.from_user.id)
    await message.answer(
        "Vehicle saved. Your garage:" if is_english(language_code) else "Автомобиль сохранён. Ваш гараж:",
        reply_markup=garage_keyboard(cars, language_code),
    )

@router.message(UserFlow.adding_vin, F.text.in_({"⏭ Не знаю VIN", "⏭ I don't know VIN"}))
async def skip_adding_vin(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    await state.set_state(UserFlow.adding_brand)
    await message.answer(
        "Okay! Write make, model, and year 👇\n_Example: Toyota Camry 2019_"
        if is_english(language_code)
        else "Хорошо! Напишите марку, модель и год автомобиля 👇\n_Пример: Toyota Camry 2019_",
        parse_mode="Markdown",
    )

@router.message(UserFlow.adding_vin, F.text)
async def receive_garage_vin(message: Message, state: FSMContext):
    clean = clean_vin(message.text)
    language_code = user_language_code(message.from_user)
    if not clean:
        await message.answer("VIN must contain 17 letters and digits. Try again or press “I don't know VIN”." if is_english(language_code) else "VIN должен состоять из 17 букв и цифр. Попробуйте ещё раз или нажмите «Не знаю VIN».")
        return

    await message.answer("Identifying the vehicle by VIN..." if is_english(language_code) else "Определяю автомобиль по VIN...")
    vehicle = await _save_car_from_vin(message, clean)
    if not vehicle:
        await state.set_state(UserFlow.adding_brand)
        await message.answer(
            "VIN accepted, but I could not identify the model.\nWrite make, model, and year manually 👇"
            if is_english(language_code)
            else "VIN принят, но модель определить не удалось.\nНапишите марку, модель и год автомобиля вручную 👇",
        )
        return

    await _show_garage(message, state)

@router.message(UserFlow.adding_brand, F.text)
async def receive_garage_vehicle_text(message: Message, state: FSMContext):
    vehicle = message.text.strip()
    language_code = user_language_code(message.from_user)
    if len(vehicle) < 2:
        await message.answer("Write make, model, and year in a bit more detail." if is_english(language_code) else "Напишите марку, модель и год чуть подробнее.")
        return
    profile = parse_vehicle_profile(vehicle)

    await add_car(
        user_id=message.from_user.id,
        vin="",
        brand=profile.brand,
        model=profile.model,
        year=profile.year,
        mileage=profile.mileage,
        engine=profile.engine,
        transmission=profile.transmission,
        fuel=profile.fuel,
        nickname=profile.nickname,
    )
    await message.answer(
        (
            f"Saved: *{escape_markdown(vehicle)}*\n\n"
            "You can also write details:\n"
            "`Toyota Camry 2019 | 120000 km | 2.5 | automatic | petrol | Camry`"
        )
        if is_english(language_code)
        else (
            f"Записал: *{escape_markdown(vehicle)}*\n\n"
            "Можно указывать расширенно:\n"
            "`Toyota Camry 2019 | 120000 км | 2.5 | автомат | бензин | Камри`"
        ),
        parse_mode="Markdown",
    )
    await _show_garage(message, state)

@router.message(UserFlow.waiting_for_vehicle, F.text.in_({"⏭ Не знаю VIN", "⏭ I don't know VIN"}))
async def skip_vin(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    await message.answer(
        "Okay! Write make, model, and year 👇\n_Example: Toyota Camry 2019_"
        if is_english(language_code)
        else "Хорошо! Напишите марку, модель и год автомобиля 👇\n_Пример: Toyota Camry 2019_",
        parse_mode="Markdown",
    )

@router.message(UserFlow.waiting_for_vehicle, F.text)
async def receive_vehicle(message: Message, state: FSMContext):
    text = message.text.strip()
    language_code = user_language_code(message.from_user)
    data = await state.get_data()
    problem = data.get("problem", "")
    issue_id = data.get("issue_id")

    clean = clean_vin(text)

    if clean:
        await message.answer("Identifying the vehicle by VIN..." if is_english(language_code) else "Определяю автомобиль по VIN...")
        vehicle = await _save_car_from_vin(message, clean)
        if not vehicle:
            vehicle = f"VIN: {clean}"
            await message.answer(
                "VIN accepted, but I could not identify the model.\nWrite make and model manually for accurate diagnostics."
                if is_english(language_code)
                else "VIN принят, но не удалось определить модель.\nНапишите марку и модель вручную для точной диагностики.",
            )
    else:
        vehicle = text
        await message.answer(
            f"Saved: *{escape_markdown(vehicle)}*" if is_english(language_code) else f"Записал: *{escape_markdown(vehicle)}*",
            parse_mode="Markdown",
        )

    await state.update_data(vehicle=vehicle)
    await state.set_state(UserFlow.helping)

    await message.answer("Refining the diagnosis..." if is_english(language_code) else "Уточняю диагноз...")
    diagnosis = await get_diagnosis(problem, vehicle, language_code)
    if issue_id:
        await update_issue(
            issue_id=issue_id,
            user_id=message.from_user.id,
            vehicle=vehicle,
            diagnosis=diagnosis,
            status="diagnosed",
        )
    await message.answer(diagnosis, reply_markup=fix_choice_keyboard(language_code))
    await ask_response_feedback(
        message,
        state,
        "Was this diagnosis helpful?" if is_english(language_code) else "Диагноз был полезен?",
        "diagnosis",
        problem,
        vehicle,
    )
