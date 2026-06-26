from utils import normalize_text_key


SERVICE_WORDS = {
    "сервис", "сто", "шиномонтаж", "эвакуатор", "запчасти", "запчасть",
    "заправка", "азс", "рядом", "ближайший", "автомойка", "мойка",
    "помыть", "детейлинг", "диагностика", "замена масла",
    "заменить масло", "поменять масло",
    "service", "repair shop", "dealer", "dealer center", "tire shop",
    "tow", "tow truck", "parts", "parts store", "gas station", "car wash",
    "detailing", "diagnostics", "oil change", "nearby", "nearest",
}

SERVICE_REQUEST_WORDS = {"найди", "найти", "где", "рядом", "ближайший", "ближайшие", "нужен", "find", "where", "nearby", "nearest", "need"}

DIY_WORDS = {
    "сам", "самому", "починить", "починю", "заменить", "снять",
    "поставить", "инструкция", "как поменять", "как починить",
    "diy", "myself", "fix myself", "repair myself", "how to fix", "how to replace",
    "instruction", "instructions",
}

GARAGE_WORDS = {"гараж", "vin", "вин", "добавить авто", "добавить машину", "garage", "add car", "my car"}
LOCATION_WORDS = {"адрес", "локация", "геолокация", "домашний адрес", "город", "address", "location", "home address", "city"}

PROBLEM_WORDS = {
    "горит", "не заводится", "не заводит", "стучит", "скрипит", "свистит",
    "течет", "течь", "дым", "запах", "дергается", "троит", "глохнет",
    "перегрев", "кипит", "ошибка", "чек", "check", "engine", "колесо",
    "шина", "тормоз", "руль", "акпп", "коробка", "масло", "антифриз",
    "аккумулятор", "стартер", "генератор", "лампа", "датчик", "звук",
    "вибрация", "педаль", "тяга", "обороты", "не едет", "плохо едет",
    "does not start", "wont start", "won't start", "knocking", "squeaking",
    "whistling", "leaking", "leak", "smoke", "smell", "shaking", "misfire",
    "stalls", "overheating", "check engine", "wheel", "tire", "brake",
    "steering", "oil", "coolant", "battery", "starter", "alternator",
    "sensor", "noise", "vibration", "pedal", "rpm", "does not drive",
}

QUESTION_WORDS = {
    "что такое", "почему", "можно ли", "сколько", "какой", "какая",
    "какие", "объясни", "расскажи",
    "what is", "why", "can i", "how much", "which", "explain", "tell me",
}


def detect_local_intent(message: str) -> str:
    text = normalize_text_key(message)
    if not text:
        return ""

    if any(word in text for word in LOCATION_WORDS):
        return "location"
    if any(word in text for word in GARAGE_WORDS) and len(text.split()) <= 4:
        return "garage"
    if any(word in text for word in SERVICE_WORDS) and any(word in text for word in SERVICE_REQUEST_WORDS):
        return "find_service"
    if any(word in text for word in DIY_WORDS):
        return "diy_repair"
    if any(word in text for word in PROBLEM_WORDS):
        return "diagnose"
    if any(word in text for word in SERVICE_WORDS):
        return "find_service"
    if any(word in text for word in QUESTION_WORDS):
        return "question"

    return ""
