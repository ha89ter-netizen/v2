from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states import UserFlow
from keyboards import main_menu_keyboard, garage_keyboard
from database import add_user, get_cars, delete_car

router = Router()

INFO_TEXT = """Вот что я умею 🔧

🚗 Диагностика по описанию проблемы
🔍 Точный диагноз под ваш автомобиль по VIN
🛠 Пошаговая инструкция как починить самостоятельно
📍 Поиск ближайших СТО, шиномонтажа, магазинов запчастей
🗺 Маршрут до сервиса прямо из бота
🏎 Гараж — храните все свои автомобили

Просто опишите проблему и мы разберёмся!"""

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await add_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.language_code or "ru"
    )
    await state.set_state(UserFlow.main_menu)
    name = message.from_user.first_name or "друг"
    await message.answer(
        f"Здравствуйте, {name}! 👋\n\n"
        "Я AutoBot — ваш личный автомобильный ассистент.\n"
        "Опишите проблему с автомобилем и я помогу разобраться 🚗",
        reply_markup=main_menu_keyboard(),
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(INFO_TEXT)

@router.message(F.text == "ℹ️ Что умеет бот")
async def btn_info(message: Message):
    await message.answer(INFO_TEXT)

@router.message(F.text == "🏠 Главное меню")
async def btn_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(UserFlow.main_menu)
    await message.answer("Главное меню 👇", reply_markup=main_menu_keyboard())

@router.message(F.text == "🔧 Новая проблема")
async def btn_new_problem(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(UserFlow.waiting_for_problem)
    await message.answer("Опишите что случилось с автомобилем 👇")

@router.message(F.text == "🚗 Мой гараж")
async def btn_garage(message: Message, state: FSMContext):
    await state.set_state(UserFlow.garage)
    cars = await get_cars(message.from_user.id)
    if cars:
        await message.answer(
            "Ваши автомобили 🚗 Выберите или добавьте новый:",
            reply_markup=garage_keyboard(cars),
        )
    else:
        await message.answer(
            "Гараж пока пустой. Добавьте свой автомобиль!",
            reply_markup=garage_keyboard([]),
        )

@router.callback_query(F.data == "add_car")
async def add_car_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserFlow.adding_vin)
    await callback.message.answer(
        "Введите VIN-код вашего автомобиля 👇\n\n"
        "_17 символов, находится на лобовом стекле или в документах_\n\n"
        "Если не знаете VIN — нажмите «Не знаю VIN»",
        parse_mode="Markdown",
    )
    await callback.answer()

@router.callback_query(F.data.startswith("select_car_"))
async def select_car_callback(callback: CallbackQuery, state: FSMContext):
    car_id = int(callback.data.split("_")[-1])
    cars = await get_cars(callback.from_user.id)
    car = next((c for c in cars if c[0] == car_id), None)

    if car:
        car_id, vin, brand, model, year = car
        vehicle = f"{brand} {model} {year} (VIN: {vin})"
        await state.update_data(vehicle=vehicle, selected_car_id=car_id)
        await state.set_state(UserFlow.waiting_for_problem)
        await callback.message.answer(
            f"Выбран *{brand} {model} {year}* 🚗\n\nОпишите проблему 👇",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )
    await callback.answer()

@router.callback_query(F.data.startswith("delete_car_"))
async def delete_car_callback(callback: CallbackQuery):
    car_id = int(callback.data.split("_")[-1])
    await delete_car(car_id)
    cars = await get_cars(callback.from_user.id)
    await callback.message.edit_reply_markup(reply_markup=garage_keyboard(cars))
    await callback.answer("Удалено!")
