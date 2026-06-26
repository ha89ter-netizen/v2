def is_english(language_code: str = "") -> bool:
    return (language_code or "").lower().startswith("en")


def user_language_code(user) -> str:
    return getattr(user, "language_code", None) or "ru"


def language_name(language_code: str = "") -> str:
    return "English" if is_english(language_code) else "Russian"


def start_text(first_name: str, language_code: str = "") -> str:
    if is_english(language_code):
        name = first_name or "friend"
        return (
            f"Hello, {name}! 👋\n\n"
            "I am AutoBot — your personal AI car assistant.\n"
            "Describe a car problem and I will help you understand what to do next 🚗"
        )

    name = first_name or "друг"
    return (
        f"Здравствуйте, {name}! 👋\n\n"
        "Я AutoBot — ваш личный автомобильный ассистент.\n"
        "Опишите проблему с автомобилем и я помогу разобраться 🚗"
    )


INFO_TEXT_RU = """Вот что я умею 🔧

🚗 Диагностика по описанию проблемы
🔍 Точный диагноз под ваш автомобиль по VIN
📷 Анализ фото приборки, колеса, течи или детали
🛠 Пошаговая инструкция как починить самостоятельно
🔩 Подбор запчастей по авто, бюджету и вероятной неисправности
📍 Поиск ближайших СТО, шиномонтажа, магазинов запчастей
🚨 Срочная помощь и поиск эвакуатора рядом
🗺 Маршрут до сервиса прямо из бота
🏎 Гараж — храните все свои автомобили
⏰ Повторяющиеся напоминания по дате и пробегу
🧪 Тестовый режим для отладки поиска и логики

Просто опишите проблему и мы разберёмся!"""


INFO_TEXT_EN = """Here is what I can do 🔧

🚗 Diagnose a car problem from your description
🔍 Give a vehicle-specific answer using VIN or garage data
📷 Analyze dashboard, tire, leak, damage, or part photos
🛠 Guide you through safe DIY repair steps
🔩 Suggest parts by vehicle, budget, and likely fault
📍 Find nearby repair shops, dealers, tire shops, and parts stores
🚨 Help with urgent roadside situations and tow search
🗺 Provide map and route links
🏎 Keep your cars in a garage
⏰ Create maintenance reminders by date or mileage
🧪 Provide test/demo flows for QA and investor demos

Just describe the problem and I will guide you through the next step."""


def info_text(language_code: str = "") -> str:
    return INFO_TEXT_EN if is_english(language_code) else INFO_TEXT_RU


def phone_launcher_text(language_code: str = "") -> str:
    launcher_url = "https://ha89ter-netizen.github.io/v2/pwa/"
    if is_english(language_code):
        return (
            "Add AutoBot to your phone home screen 📱\n\n"
            f"Open this link:\n{launcher_url}\n\n"
            "iPhone:\n"
            "1. Open the link in Safari.\n"
            "2. Tap Share.\n"
            "3. Choose Add to Home Screen.\n\n"
            "Android:\n"
            "1. Open the link in Chrome.\n"
            "2. Tap the menu.\n"
            "3. Choose Install app or Add to Home screen.\n\n"
            "After that, AutoBot will open from a phone icon and take you straight to Telegram."
        )

    return (
        "Добавьте AutoBot на главный экран телефона 📱\n\n"
        f"Откройте ссылку:\n{launcher_url}\n\n"
        "iPhone:\n"
        "1. Откройте ссылку в Safari.\n"
        "2. Нажмите «Поделиться».\n"
        "3. Выберите «На экран Домой».\n\n"
        "Android:\n"
        "1. Откройте ссылку в Chrome.\n"
        "2. Нажмите меню.\n"
        "3. Выберите «Установить приложение» или «Добавить на главный экран».\n\n"
        "После этого AutoBot будет открываться с иконки на телефоне сразу в Telegram."
    )
