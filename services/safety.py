CRITICAL_EXACT_PHRASES = {
    "brakes": [
        "не тормозит",
        "машина не тормозит",
        "тормоза отказали",
        "отказали тормоза",
        "педаль провалилась",
        "проваливается педаль",
        "педаль тормоза провалилась",
        "педаль тормоза в полу",
        "тормозная жидкость течет",
        "течь тормозной жидкости",
        "no brakes",
        "brakes failed",
        "brake pedal went to floor",
        "brake fluid leaking",
        "car does not brake",
    ],
    "steering": [
        "заклинило руль",
        "руль заклинило",
        "руль заблокировался",
        "заблокировался руль",
        "не поворачивается руль",
        "руль не поворачивается",
        "руль не крутится",
        "не могу повернуть",
        "потерял управление",
        "потеряла управление",
        "машина не управляется",
        "steering locked",
        "wheel locked",
        "cannot steer",
        "lost steering",
        "lost control",
    ],
    "wheel": [
        "колесо отвалилось",
        "отвалилось колесо",
        "лопнула шина на скорости",
        "разорвало шину",
        "болтается колесо",
        "wheel fell off",
        "tire blew out",
        "loose wheel",
    ],
    "fire_fuel": [
        "запах бензина",
        "течь бензина",
        "течет бензин",
        "топливо течет",
        "машина горит",
        "горит проводка",
        "проводка горит",
        "горит под капотом",
        "огонь",
        "дым",
        "дым из под капота",
        "дым из-под капота",
        "искрит",
        "искра",
        "smoke",
        "smoke under hood",
        "fuel smell",
        "gasoline smell",
        "fuel leak",
        "gas leaking",
        "car is on fire",
        "wiring is burning",
    ],
    "overheat": [
        "перегрев",
        "кипит",
        "температура красная",
        "пар из-под капота",
        "overheating",
        "temperature in red",
        "steam under hood",
    ],
    "oil": [
        "давление масла",
        "масленка",
        "красная лампа масла",
        "горит красная масленка",
        "нет давления масла",
        "oil pressure",
        "red oil light",
        "no oil pressure",
    ],
}

CRITICAL_COMBINATIONS = {
    "brakes": {
        "subject": ["тормоз", "тормоза", "педаль тормоза", "тормозная жидкость"],
        "danger": ["отказ", "провал", "не работает", "не срабатывает", "теч", "пустая педаль"],
    },
    "steering": {
        "subject": ["руль", "рулев"],
        "danger": ["заклин", "заблок", "не поворач", "не крут", "отказ", "потерял управление", "потеряла управление"],
    },
}

CRITICAL_WARNING = (
    "Это похоже на опасную неисправность. Не продолжайте движение, "
    "если есть риск потери управления, пожара, перегрева или отказа тормозов.\n\n"
    "Лучше остановиться в безопасном месте и найти ближайший сервис или эвакуатор."
)

CRITICAL_WARNING_EN = (
    "This looks like a dangerous fault. Do not continue driving if there is any risk "
    "of losing control, fire, overheating, or brake failure.\n\n"
    "Stop in a safe place and find the nearest service or tow truck."
)


def critical_warning(language_code: str = "") -> str:
    return CRITICAL_WARNING_EN if (language_code or "").lower().startswith("en") else CRITICAL_WARNING

def detect_safety_risk(problem: str) -> dict:
    text = problem.lower()
    matched = []

    for category, keywords in CRITICAL_EXACT_PHRASES.items():
        if any(keyword in text for keyword in keywords):
            matched.append(category)

    for category, rules in CRITICAL_COMBINATIONS.items():
        has_subject = any(word in text for word in rules["subject"])
        has_danger = any(word in text for word in rules["danger"])
        if has_subject and has_danger and category not in matched:
            matched.append(category)

    if matched:
        return {
            "risk_level": "critical",
            "matched": matched,
            "message": CRITICAL_WARNING,
        }

    return {
        "risk_level": "normal",
        "matched": [],
        "message": "",
    }
