from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime
import aiohttp

from states import UserFlow
from keyboards import (
    location_keyboard as shared_location_keyboard,
    no_places_keyboard,
    service_choice_keyboard,
    service_results_keyboard,
)
from services.places import PLACE_TYPES, search_places, format_places_message
from services.i18n import is_english, user_language_code
from config import config
from database import add_user, get_user_test_mode, record_api_usage, save_home_location, get_home_location
from services.retry import retry_async

router = Router()

ADDRESS_STEP_CITY = "city"
ADDRESS_STEP_STREET = "street"

def location_keyboard(language_code: str = ""):
    return shared_location_keyboard(language_code)

def after_location_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔄 Обновить локацию")],
            [KeyboardButton(text="🏠 Сохранить как домашний адрес")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True,
    )

def build_manual_address_query(city: str, street: str) -> str:
    parts = []
    street = street.strip()
    city = city.strip()
    if street:
        parts.append(street)
    if city:
        parts.append(city)
    if config.DEFAULT_COUNTRY:
        country = config.DEFAULT_COUNTRY.strip()
        normalized = " ".join(parts).lower()
        if country.lower() not in normalized:
            parts.append(country)
    return ", ".join(parts)

def _country_code_from_result(result: dict) -> str:
    for component in result.get("address_components", []):
        if "country" in component.get("types", []):
            return (component.get("short_name") or "").upper()
    return ""

async def geocode_address(address: str) -> tuple:
    geo_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "language": "ru",
        "key": config.GOOGLE_PLACES_API_KEY,
    }
    if config.DEFAULT_COUNTRY_CODE:
        country_code = config.DEFAULT_COUNTRY_CODE.upper()
        params["components"] = f"country:{country_code}"
        params["region"] = country_code.lower()

    async with aiohttp.ClientSession() as session:
        attempts = 1
        try:
            async def action():
                async with session.get(
                    geo_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=8)
                ) as resp:
                    return await resp.json()

            data, attempts = await retry_async(action, config.GOOGLE_MAX_RETRIES)
            ok = data.get("status") == "OK" and data.get("results")
            await record_api_usage(
                provider="google",
                operation="geocode",
                success=bool(ok),
                attempts=attempts,
                estimated_cost_usd=config.GOOGLE_GEOCODE_COST_PER_REQUEST,
                error="" if ok else data.get("status", "unknown"),
            )
            if ok:
                result = data["results"][0]
                result_country = _country_code_from_result(result)
                expected_country = config.DEFAULT_COUNTRY_CODE.upper()
                if expected_country and result_country and result_country != expected_country:
                    await record_api_usage(
                        provider="google",
                        operation="geocode_country_filter",
                        success=False,
                        attempts=1,
                        estimated_cost_usd=0,
                        error=f"expected {expected_country}, got {result_country}",
                    )
                    return None, None, address
                loc = result["geometry"]["location"]
                return loc["lat"], loc["lng"], result.get("formatted_address", address)
        except Exception as e:
            await record_api_usage(
                provider="google",
                operation="geocode",
                success=False,
                attempts=attempts,
                estimated_cost_usd=config.GOOGLE_GEOCODE_COST_PER_REQUEST,
                error=str(e),
            )
    return None, None, address

async def _show_places(message: Message, state: FSMContext, lat: float, lon: float, location_name: str):
    data = await state.get_data()
    language_code = data.get("language_code") or user_language_code(message.from_user)
    english = is_english(language_code)
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
    cat = PLACE_TYPES.get(category, PLACE_TYPES["sto"])
    radius = int(data.get("search_radius") or cat.get("radius", config.SEARCH_RADIUS))
    min_rating = float(data.get("search_min_rating") if data.get("search_min_rating") is not None else cat.get("min_rating", config.MIN_RATING))
    limit = int(data.get("place_limit") or 5)

    await message.answer("Searching nearby places..." if english else "Ищу ближайшие сервисы...")
    places = await search_places(lat, lon, category, radius=radius, min_rating=min_rating, limit=limit)
    await state.update_data(
        forced_category=category,
        search_radius=radius,
        search_min_rating=min_rating,
        place_limit=limit,
        last_places_count=len(places),
    )
    places_msg = format_places_message(places, category, location_name, language_code)
    await message.answer(
        places_msg,
        parse_mode="Markdown",
        disable_web_page_preview=False,
    )
    if await get_user_test_mode(message.from_user.id):
        await message.answer(
            "Тестовый режим:\n"
            f"Категория: {category} / {cat['label']}\n"
            f"Радиус: {radius} м\n"
            f"Мин. рейтинг: {min_rating}\n"
            f"Лимит выдачи: {limit}\n"
            f"Найдено в выдаче: {len(places)}\n"
            f"Локация: {lat}, {lon} — {location_name}"
        )
    await state.set_state(UserFlow.main_menu)
    if places:
        await message.answer("You can refine the search 👇" if english else "Можно уточнить поиск 👇", reply_markup=service_results_keyboard(language_code))
    else:
        await message.answer("What should we try next? 👇" if english else "Что попробуем дальше? 👇", reply_markup=no_places_keyboard(language_code))

async def _repeat_place_search(message: Message, state: FSMContext):
    data = await state.get_data()
    lat = data.get("lat")
    lon = data.get("lon")
    location_name = data.get("location_name", "вашего местоположения")
    language_code = data.get("language_code") or user_language_code(message.from_user)
    if lat is None or lon is None:
        await state.set_state(UserFlow.waiting_for_location)
        await message.answer("First send your location or address 👇" if is_english(language_code) else "Сначала отправьте геолокацию или адрес 👇", reply_markup=location_keyboard(language_code))
        return
    await _show_places(message, state, lat, lon, location_name)

@router.message(F.text.in_({"🔄 Обновить локацию", "🔄 Update location"}))
async def update_location(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    await state.set_state(UserFlow.waiting_for_location)
    await message.answer(
        "Send a new location 👇" if is_english(language_code) else "Отправьте новую геолокацию 👇",
        reply_markup=location_keyboard(language_code),
    )

@router.message(F.text.in_({"🏠 Сохранить как домашний адрес", "🏠 Save as home address"}))
async def save_as_home(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    data = await state.get_data()
    lat = data.get("lat")
    lon = data.get("lon")
    location_name = data.get("location_name", "")

    if lat is not None and lon is not None:
        await add_user(
            message.from_user.id,
            message.from_user.username or "",
            message.from_user.language_code or "ru",
        )
        await save_home_location(message.from_user.id, lat, lon, location_name)
        await message.answer(
            (f"Home address saved:\n📍 {location_name}" if is_english(language_code) else f"Домашний адрес сохранён:\n📍 {location_name}")
        )
    else:
        await message.answer("Send your location first." if is_english(language_code) else "Сначала отправьте геолокацию.")

@router.message(F.text.in_({"➕ Показать ещё", "➕ Show more"}))
async def show_more_places(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.update_data(place_limit=min(int(data.get("place_limit") or 5) + 3, 12))
    await _repeat_place_search(message, state)

@router.message(F.text.in_({"☎️ Контакты и маршрут", "☎️ Contacts and route"}))
async def explain_contacts_and_route(message: Message, state: FSMContext):
    data = await state.get_data()
    language_code = data.get("language_code") or user_language_code(message.from_user)
    if not data.get("last_places_count"):
        await message.answer("First I need to find places nearby. Send your location or address 👇" if is_english(language_code) else "Сначала найдём сервисы рядом. Отправьте геолокацию или адрес 👇", reply_markup=location_keyboard(language_code))
        return
    await message.answer(
        (
            "In the list above each place has a phone number, “Open on map”, and “Build route”. "
            "Tap the needed link in the place card.\n\n"
            "If there are too few options, tap “➕ Show more”."
        )
        if is_english(language_code)
        else (
            "В списке выше у каждого места есть телефон, ссылка «Открыть на карте» "
            "и «Проложить маршрут». Нажмите нужную ссылку в карточке сервиса.\n\n"
            "Если вариантов мало — нажмите «➕ Показать ещё»."
        )
    )

@router.message(F.text.in_({"📍 Искать ближе", "📍 Search closer"}))
async def search_closer_places(message: Message, state: FSMContext):
    data = await state.get_data()
    radius = int(data.get("search_radius") or config.SEARCH_RADIUS)
    await state.update_data(search_radius=max(2000, int(radius * 0.6)), place_limit=5)
    await _repeat_place_search(message, state)

@router.message(F.text.in_({"⭐ Рейтинг ниже", "⭐ Lower rating"}))
async def lower_rating_places(message: Message, state: FSMContext):
    data = await state.get_data()
    current = float(data.get("search_min_rating") if data.get("search_min_rating") is not None else config.MIN_RATING)
    await state.update_data(search_min_rating=max(0, current - 0.5), place_limit=5)
    await _repeat_place_search(message, state)

@router.message(F.text.in_({"📡 Увеличить радиус", "📡 Increase radius"}))
async def increase_radius_places(message: Message, state: FSMContext):
    data = await state.get_data()
    radius = int(data.get("search_radius") or config.SEARCH_RADIUS)
    await state.update_data(search_radius=min(radius * 2, 30000), place_limit=5)
    await _repeat_place_search(message, state)

@router.message(F.text.in_({"🔁 Поменять категорию", "🔁 Change category"}))
async def change_service_category(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    await message.answer("What type of service do you need? 👇" if is_english(language_code) else "Какой сервис нужен? 👇", reply_markup=service_choice_keyboard(language_code))

@router.message(F.text.in_({"✏️ Другой адрес", "✏️ Another address"}))
async def search_another_address(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    await state.set_state(UserFlow.waiting_for_location)
    await state.update_data(address_step=None, manual_city="")
    await message.answer("Send another location or enter an address 👇" if is_english(language_code) else "Отправьте другую геолокацию или введите адрес 👇", reply_markup=location_keyboard(language_code))

@router.message(UserFlow.waiting_for_location, F.text.in_({"🏠 Использовать домашний адрес", "🏠 Use home address"}))
async def use_home_location(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    home = await get_home_location(message.from_user.id)
    if home:
        lat, lon, name = home
        await message.answer(f"Using home address: {name}" if is_english(language_code) else f"Использую домашний адрес: {name}")
        await _show_places(message, state, lat, lon, name)
    else:
        await message.answer(
            "Home address is not saved. Enter an address manually or share your location."
            if is_english(language_code)
            else "Домашний адрес не сохранён. Введите адрес вручную или поделитесь геолокацией."
        )

@router.message(UserFlow.waiting_for_location, F.location)
async def receive_location_geo(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    lat = message.location.latitude
    lon = message.location.longitude
    await message.answer("Location received!" if is_english(language_code) else "Геолокация получена!")
    await _show_places(message, state, lat, lon, "your location" if is_english(language_code) else "вашего местоположения")

@router.message(UserFlow.waiting_for_location, F.text.in_({"✏️ Ввести адрес вручную", "✏️ Enter address manually"}))
async def btn_enter_address(message: Message, state: FSMContext):
    language_code = user_language_code(message.from_user)
    await state.update_data(address_step=ADDRESS_STEP_CITY, manual_city="")
    await message.answer(
        "First write the city 👇\n\nExample: Almaty, Astana, Shymkent."
        if is_english(language_code)
        else "Сначала напишите город 👇\n\nНапример: Алматы, Астана, Шымкент."
    )

@router.message(UserFlow.waiting_for_location, F.text)
async def receive_location_text(message: Message, state: FSMContext):
    address = message.text.strip()
    data = await state.get_data()
    language_code = data.get("language_code") or user_language_code(message.from_user)
    english = is_english(language_code)
    address_step = data.get("address_step")

    if len(address) < 2:
        await message.answer("Please write the address in more detail 🙏" if english else "Пожалуйста напишите адрес подробнее 🙏")
        return

    if address_step == ADDRESS_STEP_CITY:
        await state.update_data(address_step=ADDRESS_STEP_STREET, manual_city=address)
        await message.answer(
            "Now write the street, district, or exact address 👇\n\nExample: Abay 10 or Bostandyk district."
            if english
            else "Теперь напишите улицу, район или точный адрес 👇\n\nНапример: Абая 10 или Бостандыкский район."
        )
        return

    if address_step == ADDRESS_STEP_STREET:
        city = data.get("manual_city", "")
        address_query = build_manual_address_query(city, address)
        await state.update_data(address_step=None, manual_city="")
    else:
        address_query = build_manual_address_query("", address)

    lat, lon, formatted = await geocode_address(address_query)

    if lat is not None and lon is not None:
        await message.answer(f"Found: {formatted}" if english else f"Нашёл: {formatted}")
        await _show_places(message, state, lat, lon, formatted)
    else:
        await message.answer(
            "Could not recognize the address. Try writing it more precisely."
            if english
            else "Не удалось определить адрес. Попробуйте написать точнее."
        )
