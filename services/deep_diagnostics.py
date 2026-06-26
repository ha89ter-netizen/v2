from dataclasses import dataclass

from services.i18n import is_english
from utils import normalize_text_key


@dataclass(frozen=True)
class DiagnosticProfile:
    system: str
    title_ru: str
    title_en: str
    questions_ru: tuple[str, ...]
    questions_en: tuple[str, ...]


PROFILES = {
    "engine": DiagnosticProfile(
        "engine",
        "двигатель / зажигание / топливо",
        "engine / ignition / fuel",
        (
            "На холодную, на горячую или всегда?",
            "Симптом сильнее на холостых, при разгоне или на скорости?",
            "Горит ли Check Engine? Есть ли ошибки OBD?",
            "Есть ли запах бензина, дым, хлопки или повышенный расход?",
        ),
        (
            "Cold engine, warm engine, or always?",
            "Is it worse at idle, during acceleration, or at speed?",
            "Is Check Engine on? Any OBD codes?",
            "Any fuel smell, smoke, popping, or higher fuel consumption?",
        ),
    ),
    "brake": DiagnosticProfile(
        "brake",
        "тормозная система",
        "brake system",
        (
            "Скрип, вибрация, мягкая педаль или машина плохо тормозит?",
            "Симптом при лёгком торможении или при сильном?",
            "Есть ли увод в сторону или запах гари после торможения?",
            "Когда меняли колодки/диски/тормозную жидкость?",
        ),
        (
            "Squeak, vibration, soft pedal, or poor braking?",
            "Does it happen under light braking or hard braking?",
            "Any pull to one side or burning smell after braking?",
            "When were pads/rotors/brake fluid last changed?",
        ),
    ),
    "suspension": DiagnosticProfile(
        "suspension",
        "подвеска / рулевое",
        "suspension / steering",
        (
            "Стук на кочках, при повороте или при торможении?",
            "Звук спереди, сзади, слева или справа?",
            "Машину тянет в сторону или руль стоит криво?",
            "Есть ли вибрация на скорости?",
        ),
        (
            "Knock over bumps, while turning, or while braking?",
            "Front, rear, left, or right side?",
            "Does the car pull to one side or is the steering wheel crooked?",
            "Any vibration at speed?",
        ),
    ),
    "electric": DiagnosticProfile(
        "electric",
        "электрика / запуск",
        "electrical / starting",
        (
            "Стартер крутит или только щёлкает?",
            "Приборка горит ярко или тускло?",
            "Проблема появилась после простоя, мороза или мойки?",
            "Проверяли клеммы, АКБ, генератор?",
        ),
        (
            "Does the starter crank or only click?",
            "Are dashboard lights bright or dim?",
            "Did it happen after parking, cold weather, or washing?",
            "Have battery terminals, battery, or alternator been checked?",
        ),
    ),
    "cooling": DiagnosticProfile(
        "cooling",
        "охлаждение / перегрев",
        "cooling / overheating",
        (
            "Температура растёт в пробке, на трассе или всегда?",
            "Работает ли вентилятор радиатора?",
            "Уходит ли антифриз? Есть ли течь или пар?",
            "Печка дует горячим воздухом?",
        ),
        (
            "Temperature rises in traffic, on highway, or always?",
            "Does the radiator fan work?",
            "Is coolant disappearing? Any leak or steam?",
            "Does the cabin heater blow hot air?",
        ),
    ),
    "transmission": DiagnosticProfile(
        "transmission",
        "АКПП / трансмиссия",
        "automatic transmission / drivetrain",
        (
            "Есть пинки при переключении, пробуксовка или задержка?",
            "На холодную или после прогрева?",
            "На какой скорости/передаче сильнее?",
            "Когда меняли масло в коробке?",
        ),
        (
            "Any shift kicks, slipping, or delay?",
            "Cold or after warming up?",
            "At what speed/gear is it worse?",
            "When was transmission fluid changed?",
        ),
    ),
    "general": DiagnosticProfile(
        "general",
        "общая диагностика",
        "general diagnostics",
        (
            "Когда именно проявляется симптом?",
            "Есть ли звук, запах, дым, течь или ошибка на панели?",
            "Симптом постоянный или появляется иногда?",
            "Что уже проверяли или меняли?",
        ),
        (
            "When exactly does the symptom appear?",
            "Any sound, smell, smoke, leak, or dashboard warning?",
            "Is it constant or intermittent?",
            "What has already been checked or replaced?",
        ),
    ),
}


def detect_diagnostic_system(problem: str) -> str:
    text = normalize_text_key(problem)
    if any(word in text for word in ("тормоз", "колод", "диск", "педаль", "brake", "pads", "rotor")):
        return "brake"
    if any(word in text for word in ("подвес", "стойк", "амортиз", "шаровая", "руль", "стук", "suspension", "shock", "strut", "steering", "knock")):
        return "suspension"
    if any(word in text for word in ("акб", "аккумулятор", "стартер", "генератор", "электр", "battery", "starter", "alternator", "electrical")):
        return "electric"
    if any(word in text for word in ("перегрев", "кипит", "антифриз", "радиатор", "температур", "overheat", "coolant", "radiator", "temperature")):
        return "cooling"
    if any(word in text for word in ("акпп", "короб", "передач", "вариатор", "transmission", "gear", "cvt", "automatic")):
        return "transmission"
    if any(word in text for word in ("троит", "тряс", "чек", "двиг", "холост", "свеч", "катуш", "форсунк", "бензонасос", "engine", "misfire", "rough idle", "shakes", "check engine", "injector", "fuel pump")):
        return "engine"
    return "general"


def diagnostic_profile(problem: str) -> DiagnosticProfile:
    return PROFILES[detect_diagnostic_system(problem)]


def diagnostic_signal_score(problem: str) -> int:
    text = normalize_text_key(problem)
    signal_groups = (
        ("холод", "горяч", "после прогрева", "cold", "warm", "hot"),
        ("холост", "разгон", "скорост", "тормож", "поворот", "idle", "acceleration", "speed", "braking", "turning"),
        ("чек", "ошибка", "obd", "check engine", "code"),
        ("дым", "запах", "течь", "пар", "smoke", "smell", "leak", "steam"),
        ("стук", "скрип", "свист", "вибрац", "knock", "squeak", "whistle", "vibration"),
        ("педаль", "руль", "температур", "обороты", "pedal", "steering", "temperature", "rpm"),
    )
    score = 0
    for group in signal_groups:
        if any(signal in text for signal in group):
            score += 1
    if len(text.split()) >= 8:
        score += 1
    return score


def needs_quick_clarification(problem: str) -> bool:
    return diagnostic_signal_score(problem) < 2


def quick_question_text(problem: str, language_code: str = "") -> str:
    profile = diagnostic_profile(problem)
    english = is_english(language_code)
    title = profile.title_en if english else profile.title_ru
    questions = profile.questions_en if english else profile.questions_ru
    question = questions[0]
    if english:
        return (
            f"To avoid guessing, one quick question.\n"
            f"System: {title}.\n\n"
            f"{question}\n\n"
            "You can also press “Skip details”."
        )
    return (
        f"Чтобы не гадать, один короткий вопрос.\n"
        f"Система: {title}.\n\n"
        f"{question}\n\n"
        "Можно нажать «Пропустить уточнение»."
    )


def diagnostic_questions_text(problem: str, language_code: str = "") -> str:
    profile = diagnostic_profile(problem)
    english = is_english(language_code)
    title = profile.title_en if english else profile.title_ru
    questions = profile.questions_en if english else profile.questions_ru
    if english:
        header = f"Deep diagnostic mode.\nSystem: {title}.\n\nReply in one message:"
    else:
        header = f"Глубокий режим диагностики.\nСистема: {title}.\n\nОтветьте одним сообщением:"
    lines = [header]
    lines.extend(f"{index}. {question}" for index, question in enumerate(questions, 1))
    if english:
        lines.append("\nIf you do not know, press “Skip details”.")
    else:
        lines.append("\nЕсли не знаете — нажмите «Пропустить уточнение».")
    return "\n".join(lines)


def enrich_problem_context(problem: str, onset: str = "", details: str = "", language_code: str = "") -> str:
    profile = diagnostic_profile(problem)
    if is_english(language_code):
        lines = [
            problem,
            "",
            f"Likely system: {profile.title_en}.",
        ]
        if onset:
            lines.append(f"Problem onset: {onset}.")
        if details:
            lines.append(f"User diagnostic details: {details}.")
        return "\n".join(lines).strip()

    lines = [
        problem,
        "",
        f"Вероятная система: {profile.title_ru}.",
    ]
    if onset:
        lines.append(f"Динамика проблемы: {onset}.")
    if details:
        lines.append(f"Уточнения пользователя: {details}.")
    return "\n".join(lines).strip()
