from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
)
from services.service_categories import SERVICE_BUTTON_ROWS, SERVICE_BUTTON_ROWS_EN
from services.demo import demo_labels
from services.i18n import is_english

MAIN_MENU_RU = [
    ["🔧 Описать проблему", "🔩 Найти запчасть"],
    ["📍 Найти сервис рядом", "🚗 Мой гараж"],
    ["📷 Фото", "🚨 Срочная помощь"],
    ["⏰ Напоминания", "📜 История"],
    ["📱 На телефон", "ℹ️ Что умеет бот"],
]

MAIN_MENU_EN = [
    ["🔧 Describe problem", "🔩 Find part"],
    ["📍 Find service nearby", "🚗 My garage"],
    ["📷 Photo", "🚨 Emergency help"],
    ["⏰ Reminders", "📜 History"],
    ["📱 Add to phone", "ℹ️ What can you do"],
]

def main_menu_keyboard(language_code: str = ""):
    rows = MAIN_MENU_EN if is_english(language_code) else MAIN_MENU_RU
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=label) for label in row]
            for row in rows
        ],
        resize_keyboard=True,
    )

def garage_keyboard(cars: list, language_code: str = "") -> InlineKeyboardMarkup:
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
    add_label = "➕ Add car" if is_english(language_code) else "➕ Добавить машину"
    buttons.append([InlineKeyboardButton(text=add_label, callback_data="add_car")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def _rows(rows: list[list[str]]) -> list[list[KeyboardButton]]:
    return [[KeyboardButton(text=label) for label in row] for row in rows]


def fix_choice_keyboard(language_code: str = ""):
    rows = [
        ["🔩 Find suitable part"],
        ["🔍 Analyze deeper"],
        ["🚦 Can I drive?"],
        ["🔍 Add vehicle"],
        ["🔧 I'll fix it"],
        ["🏪 Find service"],
        ["🏠 Main menu"],
    ] if is_english(language_code) else [
        ["🔩 Найти подходящую запчасть"],
        ["🔍 Глубже разобрать"],
        ["🚦 Можно ли ехать?"],
        ["🔍 Уточнить по авто"],
        ["🔧 Сам починю"],
        ["🏪 Найди сервис"],
        ["🏠 Главное меню"],
    ]
    return ReplyKeyboardMarkup(
        keyboard=_rows(rows),
        resize_keyboard=True,
    )

def diagnosis_parts_keyboard(part_name: str = "", language_code: str = ""):
    if is_english(language_code):
        find_text = f"🔩 Find {part_name}" if part_name else "🔩 Find suitable part"
        rows = [
            [find_text],
            ["🔩 Find suitable part"],
            ["🚦 Can I drive?"],
            ["🔧 Continue diagnosis"],
            ["📍 Service nearby"],
            ["🏠 Main menu"],
        ]
    else:
        find_text = f"🔩 Найти {part_name}" if part_name else "🔩 Найти подходящую запчасть"
        rows = [
            [find_text],
            ["🔩 Найти подходящую запчасть"],
            ["🚦 Можно ли ехать?"],
            ["🔧 Продолжить диагностику"],
            ["📍 Сервис рядом"],
            ["🏠 Главное меню"],
        ]
    return ReplyKeyboardMarkup(
        keyboard=_rows(rows),
        resize_keyboard=True,
    )

def parts_budget_keyboard(language_code: str = ""):
    rows = [
        ["up to 20 000 ₸", "up to 50 000 ₸"],
        ["up to 100 000 ₸", "no limit"],
        ["🏠 Main menu"],
    ] if is_english(language_code) else [
        ["до 20 000 ₸", "до 50 000 ₸"],
        ["до 100 000 ₸", "без ограничений"],
        ["🏠 Главное меню"],
    ]
    return ReplyKeyboardMarkup(
        keyboard=_rows(rows),
        resize_keyboard=True,
        one_time_keyboard=True,
    )

def parts_after_result_keyboard(language_code: str = ""):
    rows = [
        ["🔧 I'll fix it", "🔩 Parts store nearby"],
        ["📍 Service nearby"],
        ["🔩 Find another part"],
        ["🏠 Main menu"],
    ] if is_english(language_code) else [
        ["🔧 Сам починю", "🔩 Магазин запчастей рядом"],
        ["📍 Сервис рядом"],
        ["🔩 Найти другую запчасть"],
        ["🏠 Главное меню"],
    ]
    return ReplyKeyboardMarkup(
        keyboard=_rows(rows),
        resize_keyboard=True,
    )

def urgent_help_keyboard(language_code: str = ""):
    rows = [
        ["🚨 Tow truck / urgent help"],
        ["🏪 Find service"],
        ["🏠 Main menu"],
    ] if is_english(language_code) else [
        ["🚨 Эвакуатор / срочная помощь"],
        ["🏪 Найди сервис"],
        ["🏠 Главное меню"],
    ]
    return ReplyKeyboardMarkup(
        keyboard=_rows(rows),
        resize_keyboard=True,
    )

def service_choice_keyboard(language_code: str = ""):
    rows = SERVICE_BUTTON_ROWS_EN if is_english(language_code) else SERVICE_BUTTON_ROWS
    return ReplyKeyboardMarkup(
        keyboard=_rows(rows),
        resize_keyboard=True,
        one_time_keyboard=True,
    )

def service_results_keyboard(language_code: str = ""):
    rows = [
        ["☎️ Contacts and route", "➕ Show more"],
        ["📍 Search closer"],
        ["⭐ Lower rating", "🔁 Change category"],
        ["🏠 Save as home address"],
        ["✏️ Another address", "🏠 Main menu"],
    ] if is_english(language_code) else [
        ["☎️ Контакты и маршрут", "➕ Показать ещё"],
        ["📍 Искать ближе"],
        ["⭐ Рейтинг ниже", "🔁 Поменять категорию"],
        ["🏠 Сохранить как домашний адрес"],
        ["✏️ Другой адрес", "🏠 Главное меню"],
    ]
    return ReplyKeyboardMarkup(
        keyboard=_rows(rows),
        resize_keyboard=True,
    )

def no_places_keyboard(language_code: str = ""):
    rows = [
        ["📡 Increase radius", "⭐ Lower rating"],
        ["🔁 Change category", "✏️ Another address"],
        ["🏠 Main menu"],
    ] if is_english(language_code) else [
        ["📡 Увеличить радиус", "⭐ Рейтинг ниже"],
        ["🔁 Поменять категорию", "✏️ Другой адрес"],
        ["🏠 Главное меню"],
    ]
    return ReplyKeyboardMarkup(
        keyboard=_rows(rows),
        resize_keyboard=True,
    )

def location_keyboard(language_code: str = ""):
    rows = [
        ["📍 Share location"],
        ["🏠 Use home address"],
        ["✏️ Enter address manually"],
    ] if is_english(language_code) else [
        ["📍 Поделиться геолокацией"],
        ["🏠 Использовать домашний адрес"],
        ["✏️ Ввести адрес вручную"],
    ]
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=label,
                    request_location=label in {"📍 Поделиться геолокацией", "📍 Share location"},
                )
                for label in row
            ]
            for row in rows
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

def vin_skip_keyboard(language_code: str = ""):
    label = "⏭ I don't know VIN" if is_english(language_code) else "⏭ Не знаю VIN"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=label)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

def diy_help_keyboard(language_code: str = ""):
    rows = [
        ["✅ Fixed it"],
        ["❓ It did not work"],
        ["📜 Save repair to history"],
        ["🏪 Find service"],
        ["🏠 Main menu"],
    ] if is_english(language_code) else [
        ["✅ Починил!"],
        ["❓ Не получается"],
        ["📜 Сохранить ремонт в историю"],
        ["🏪 Найди сервис"],
        ["🏠 Главное меню"],
    ]
    return ReplyKeyboardMarkup(
        keyboard=_rows(rows),
        resize_keyboard=True,
    )

def diy_troubleshoot_keyboard(language_code: str = ""):
    rows = [
        ["🧭 Continue repair"],
        ["📜 Save repair to history"],
        ["🏪 Find service"],
        ["🏠 Main menu"],
    ] if is_english(language_code) else [
        ["🧭 Продолжить ремонт"],
        ["📜 Сохранить ремонт в историю"],
        ["🏪 Найди сервис"],
        ["🏠 Главное меню"],
    ]
    return ReplyKeyboardMarkup(
        keyboard=_rows(rows),
        resize_keyboard=True,
    )

def photo_action_keyboard(language_code: str = ""):
    rows = [
        ["🔍 Clarify photo"],
        ["🔧 What can I do myself"],
        ["🏪 Find service"],
        ["📜 Save to history"],
        ["🏠 Main menu"],
    ] if is_english(language_code) else [
        ["🔍 Уточнить по фото"],
        ["🔧 Что сделать самому"],
        ["🏪 Найди сервис"],
        ["📜 Сохранить в историю"],
        ["🏠 Главное меню"],
    ]
    return ReplyKeyboardMarkup(
        keyboard=_rows(rows),
        resize_keyboard=True,
    )

def success_keyboard(language_code: str = ""):
    rows = [
        ["🔧 New problem"],
        ["🏠 Main menu"],
    ] if is_english(language_code) else [
        ["🔧 Новая проблема"],
        ["🏠 Главное меню"],
    ]
    return ReplyKeyboardMarkup(
        keyboard=_rows(rows),
        resize_keyboard=True,
    )

def problem_onset_keyboard(language_code: str = ""):
    rows = [
        ["⚡ Suddenly", "📈 Gradually"],
        ["❔ Not sure", "🏠 Main menu"],
    ] if is_english(language_code) else [
        ["⚡ Внезапно", "📈 Постепенно"],
        ["❔ Не знаю", "🏠 Главное меню"],
    ]
    return ReplyKeyboardMarkup(
        keyboard=_rows(rows),
        resize_keyboard=True,
        one_time_keyboard=True,
    )

def diagnostic_details_keyboard(language_code: str = ""):
    rows = [
        ["⏭ Skip details"],
        ["🏠 Main menu"],
    ] if is_english(language_code) else [
        ["⏭ Пропустить уточнение"],
        ["🏠 Главное меню"],
    ]
    return ReplyKeyboardMarkup(
        keyboard=_rows(rows),
        resize_keyboard=True,
        one_time_keyboard=True,
    )

def demo_keyboard(language_code: str = ""):
    labels = demo_labels(language_code)
    rows = [[KeyboardButton(text=label)] for label in labels]
    rows.append([KeyboardButton(text="🏠 Main menu" if is_english(language_code) else "🏠 Главное меню")])
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
    )

def admin_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Админ статистика"), KeyboardButton(text="💸 API расходы")],
            [KeyboardButton(text="⚠️ API ошибки"), KeyboardButton(text="👥 Пользователи")],
            [KeyboardButton(text="🔧 Частые проблемы"), KeyboardButton(text="👎 Плохие ответы")],
            [KeyboardButton(text="🧪 Тестовый режим")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True,
    )

def response_feedback_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👍 Помогло", callback_data="feedback:helpful"),
            InlineKeyboardButton(text="👎 Не помогло", callback_data="feedback:not_helpful"),
        ]
    ])

def photo_context_keyboard(language_code: str = ""):
    rows = [
        ["⚠️ Dashboard warning"],
        ["🛞 Wheel or tire"],
        ["💧 Leak or fluid"],
        ["🔧 Under-hood part"],
        ["🚗 Body damage"],
        ["📷 Other photo"],
    ] if is_english(language_code) else [
        ["⚠️ Ошибка на панели"],
        ["🛞 Колесо или шина"],
        ["💧 Течь или жидкость"],
        ["🔧 Деталь под капотом"],
        ["🚗 Кузов или повреждение"],
        ["📷 Другое фото"],
    ]
    return ReplyKeyboardMarkup(
        keyboard=_rows(rows),
        resize_keyboard=True,
        one_time_keyboard=True,
    )

def remove_keyboard():
    return ReplyKeyboardRemove()
