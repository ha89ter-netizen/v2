from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import aiohttp

from states import UserFlow
from keyboards import fix_choice_keyboard
from services.openai_ai import get_diagnosis
from database import add_car

router = Router()

async def decode_vin(vin: str) -> dict | None:
    if len(vin) != 17:
        return None

    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{vin}?format=json"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                data = await resp.json()
                results = data.get("Results", [])

                info = {}
                for item in results:
                    if item["Variable"] == "Make":
                        info["manufacturer"] = item["Value"] or "Неизвестно"
                    if item["Variable"] == "Model":
                        info["model"] = item["Value"] or ""
                    if item["Variable"] == "Model Year":
                        info["year"] = item["Value"] or "Неизвестен"

                if info.get("manufacturer"):
                    info["vin"] = vin.upper()
                    return info
        except Exception:
            return None
    return None

@router.message(UserFlow.waiting_for_vehicle, F.text == "⏭ Не знаю VIN")
async def skip_vin(message: Message, state: FSMContext):
    await message.answer(
        "Хорошо! Напишите марку, модель и год автомобиля 👇\n"
        "_Пример: Toyota Camry 2019_",
        parse_mode="Markdown",
    )

@router.message(UserFlow.waiting_for_vehicle, F.text)
async def receive_vehicle(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    problem = data.get("problem", "")
    user_id = message.from_user.id

    clean = text.upper().replace(" ", "").replace("-", "")

    if len(clean) == 17 and clean.isalnum():
        await message.answer("Определяю автомобиль по VIN...")
        vin_info = await decode_vin(clean)

        if vin_info:
            brand = vin_info.get("manufacturer", "")
            model = vin_info.get("model", "")
            year = vin_info.get("year", "")
            vehicle = f"{brand} {model} {year} (VIN: {clean})"

            await add_car(
                user_id=user_id,
                vin=clean,
                brand=brand,
                model=model,
                year=str(year),
            )

            await message.answer(
                f"Автомобиль определён:\n"
                f"Марка: *{brand}*\n"
                f"Модель: *{model}*\n"
                f"Год: *{year}*\n"
                f"VIN: `{clean}`\n\n"
                f"Автомобиль сохранён в гараж!",
                parse_mode="Markdown",
            )
        else:
            vehicle = f"VIN: {clean}"
            await message.answer(
                "VIN принят, но не удалось определить модель.\n"
                "Напишите марку и модель вручную для точной диагностики.",
            )
    else:
        vehicle = text
        await message.answer(
            f"Записал: *{vehicle}*",
            parse_mode="Markdown",
        )

    await state.update_data(vehicle=vehicle)
    await state.set_state(UserFlow.helping)

    await message.answer("Уточняю диагноз...")
    diagnosis = await get_diagnosis(problem, vehicle)
    await message.answer(diagnosis, reply_markup=fix_choice_keyboard())
