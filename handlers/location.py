from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
import aiohttp

from states import UserFlow
from keyboards import main_menu_keyboard
from services.places import search_places, format_places_message, PLACE_TYPES
from config import config
from database import save_home_location, get_home_location

router = Router()

def location_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Поделиться геолокацией", request_location=True)],
            [KeyboardButton(text="🏠 Использовать домашний адрес")],
            [KeyboardButton(text="✏️ Ввести адрес вручную")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

def after_location_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔄 Обновить локацию")],
            [KeyboardButton(text="🏠 Сохранить как домашний адрес")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True,
    )

async def geocode_address(address: str) -> tuple:
    geo_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "language": "ru",
        "key": config.GOOGLE_PLACES_API_KEY,
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                geo_url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=8)
            ) as resp:
                data = await resp.json()
                if data.get("status") == "OK" and data.get("results"):
                    result = data["results"][0]
                    loc = result["geometry"]["location"]
                    return loc["lat"], loc["lng"], result.get("formatted_address", address)
        except Exception:
            pass
    return None, None, address

async def _show_places(message: Message, state: FSMContext, lat: float, lon: float, location_name: str):
    data = await state.get_data()
    problem = data.get("problem", "")
    forced_category = data.get("forced_category")

    # Сохраняем локацию с временем
    await state.update_data(
        lat=lat,
        lon=lon,
        location_name=location_name,
        has_geo=True,
        location_time=datetime.now().isoformat(),
    )

    from services.places import detect_category
    category = forced_category or detect_category(problem)

    await message.answer("Ищу ближайшие сервисы...")
    places = await search_places(lat, lon, category)
    places_msg = format_places_message(places, category, location_name)
    await message.answer(
        places_msg,
        parse_mode="Markdown",
        disable_web_page_preview=False,
    )
    await state.set_state(UserFlow.main_menu)
    await message.answer(
        "Если остались вопросы — готов помочь!",
        reply_markup=after_location_keyboard(),
    )

@router.message(F.text == "🔄 Обновить локацию")
async def update_location(message: Message, state: FSMContext):
    await state.set_state(UserFlow.waiting_for_location)
    await message.answer(
        "Отправьте новую геолокацию 👇",
        reply_markup=location_keyboard(),
    )

@router.message(F.text == "🏠 Сохранить как домашний адрес")
async def save_as_home(message: Message, state: FSMContext):
    data = await state.get_data()
    lat = data.get("lat")
    lon = data.get("lon")
    location_name = data.get("location_name", "")

    if lat and lon:
        await save_home_location(message.from_user.id, lat, lon, location_name)
        await message.answer(
            f"Домашний адрес сохранён:\n📍 {location_name}"
        )
    else:
        await message.answer("Сначала отправьте геолокацию.")

@router.message(UserFlow.waiting_for_location, F.text == "🏠 Использовать домашний адрес")
async def use_home_location(message: Message, state: FSMContext):
    home = await get_home_location(message.from_user.id)
    if home:
        lat, lon, name = home
        await message.answer(f"Использую домашний адрес: {name}")
        await _show_places(message, state, lat, lon, name)
    else:
        await message.answer(
            "Домашний адрес не сохранён. Введите адрес вручную или поделитесь геолокацией."
        )

@router.message(UserFlow.waiting_for_location, F.location)
async def receive_location_geo(message: Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude
    await message.answer("Геолокация получена!")
    await _show_places(message, state, lat, lon, "вашего местоположения")

@router.message(UserFlow.waiting_for_location, F.text == "✏️ Ввести адрес вручную")
async def btn_enter_address(message: Message):
    await message.answer("Напишите ваш город или адрес 👇")

@router.message(UserFlow.waiting_for_location, F.text)
async def receive_location_text(message: Message, state: FSMContext):
    address = message.text.strip()

    if len(address) < 2:
        await message.answer("Пожалуйста напишите адрес подробнее 🙏")
        return

    lat, lon, formatted = await geocode_address(address)

    if lat:
        await message.answer(f"Нашёл: {formatted}")
        await _show_places(message, state, lat, lon, formatted)
    else:
        await message.answer(
            "Не удалось определить адрес. Попробуйте написать точнее."
        )

