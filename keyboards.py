from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
)

def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔧 Описать проблему")],
            [KeyboardButton(text="🚗 Мой гараж")],
            [KeyboardButton(text="📍 Найти сервис рядом")],
            [KeyboardButton(text="ℹ️ Что умеет бот")],
        ],
        resize_keyboard=True,
    )

def garage_keyboard(cars: list) -> InlineKeyboardMarkup:
    buttons = []
    for car in cars:
        car_id, vin, brand, model, year = car
        buttons.append([
            InlineKeyboardButton(
                text=f"🚗 {brand} {model} {year}",
                callback_data=f"select_car_{car_id}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"delete_car_{car_id}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="➕ Добавить машину", callback_data="add_car")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def fix_choice_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔧 Сам починю")],
            [KeyboardButton(text="🏪 Найди сервис")],
        ],
        resize_keyboard=True,
    )

def location_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Поделиться геолокацией", request_location=True)],
            [KeyboardButton(text="✏️ Ввести адрес вручную")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

def vin_skip_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏭ Не знаю VIN")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

def diy_help_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Починил!")],
            [KeyboardButton(text="❓ Не получается")],
            [KeyboardButton(text="🏪 Найди сервис")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True,
    )

def success_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔧 Новая проблема")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True,
    )

def remove_keyboard():
    return ReplyKeyboardRemove()
