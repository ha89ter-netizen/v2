from dataclasses import dataclass

from utils import normalize_text_key


@dataclass(frozen=True)
class PartDefinition:
    key: str
    name_ru: str
    name_en: str
    system: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class PartCandidate:
    part: PartDefinition
    confidence: int
    reason: str = ""


PARTS = {
    "ignition_coil": PartDefinition(
        "ignition_coil",
        "катушка зажигания",
        "ignition coil",
        "ignition",
        ("катушка", "катушка зажигания", "троит", "трясет", "пропуски зажигания", "ignition coil", "misfire", "engine shakes", "rough idle"),
    ),
    "spark_plug": PartDefinition(
        "spark_plug",
        "свеча зажигания",
        "spark plug",
        "ignition",
        ("свеча", "свечи", "свеча зажигания", "плохо заводится", "троит", "spark plug", "spark plugs", "hard start", "rough idle"),
    ),
    "injector": PartDefinition(
        "injector",
        "форсунка",
        "fuel injector",
        "fuel",
        ("форсунка", "форсунки", "впрыск", "подача топлива", "injector", "fuel injector", "fuel injection"),
    ),
    "brake_pads": PartDefinition(
        "brake_pads",
        "тормозные колодки",
        "brake pads",
        "brake",
        ("колодки", "тормозные колодки", "скрип тормоз", "пищат тормоза", "brake pads", "squeaking brakes", "brake squeal"),
    ),
    "brake_disc": PartDefinition(
        "brake_disc",
        "тормозной диск",
        "brake rotor",
        "brake",
        ("тормозной диск", "диски", "биение при торможении", "brake rotor", "brake disc", "vibration when braking"),
    ),
    "shock_absorber": PartDefinition(
        "shock_absorber",
        "амортизатор",
        "shock absorber",
        "suspension",
        ("амортизатор", "стойка", "стук подвески", "раскачивает", "shock absorber", "strut", "suspension knocking", "bouncy ride"),
    ),
    "ball_joint": PartDefinition(
        "ball_joint",
        "шаровая опора",
        "ball joint",
        "suspension",
        ("шаровая", "шаровая опора", "люфт", "стук на кочках", "ball joint", "play in suspension", "knock over bumps"),
    ),
    "headlight": PartDefinition(
        "headlight",
        "фара",
        "headlight",
        "body",
        ("фара", "фары", "свет", "не горит фара", "headlight", "headlamp", "light not working"),
    ),
    "fuel_pump": PartDefinition(
        "fuel_pump",
        "бензонасос",
        "fuel pump",
        "fuel",
        ("бензонасос", "топливный насос", "насос топлива", "нет давления топлива", "fuel pump", "no fuel pressure"),
    ),
    "battery": PartDefinition(
        "battery",
        "аккумулятор",
        "battery",
        "electric",
        ("аккумулятор", "акб", "сел аккумулятор", "не крутит стартер", "battery", "dead battery", "starter does not crank"),
    ),
    "oxygen_sensor": PartDefinition(
        "oxygen_sensor",
        "датчик кислорода",
        "oxygen sensor",
        "engine",
        ("лямбда", "датчик кислорода", "датчик", "ошибка смеси", "oxygen sensor", "lambda sensor", "mixture code"),
    ),
}

SAFETY_SYSTEMS = {"brake", "steering", "suspension", "fuel"}


def classify_part_request(text: str) -> PartCandidate:
    candidates = infer_part_candidates(text)
    if candidates:
        return candidates[0]
    unknown = PartDefinition("unknown", "неизвестная деталь", "unknown part", "unknown", ())
    return PartCandidate(unknown, 0, "Не удалось уверенно определить тип детали.")


def infer_part_candidates(*texts: str) -> list[PartCandidate]:
    text = normalize_text_key(" ".join(value for value in texts if value))
    if not text:
        return []

    scored: dict[str, int] = {}
    reasons: dict[str, str] = {}
    for key, part in PARTS.items():
        score = 0
        for alias in part.aliases:
            alias_key = normalize_text_key(alias)
            if alias_key and alias_key in text:
                score += 35 if len(alias_key.split()) > 1 else 25
        if score:
            scored[key] = min(score, 90)
            reasons[key] = "Найдено совпадение по симптомам или названию детали."

    if any(word in text for word in ("трясет", "троит", "холост", "пропуски", "дергается", "shakes", "rough idle", "misfire", "jerks")):
        scored["ignition_coil"] = max(scored.get("ignition_coil", 0), 70)
        scored["spark_plug"] = max(scored.get("spark_plug", 0), 20)
        scored["injector"] = max(scored.get("injector", 0), 10)
        reasons["ignition_coil"] = "Тряска/троение часто связаны с катушкой зажигания."
    if any(word in text for word in ("скрип", "пищат", "тормоз", "squeak", "squeal", "brake")):
        scored["brake_pads"] = max(scored.get("brake_pads", 0), 70)
        scored["brake_disc"] = max(scored.get("brake_disc", 0), 20)
    if any(word in text for word in ("стук", "кочка", "подвес", "knock", "bump", "suspension")):
        scored["shock_absorber"] = max(scored.get("shock_absorber", 0), 55)
        scored["ball_joint"] = max(scored.get("ball_joint", 0), 45)
    if any(word in text for word in ("не завод", "топлив", "давлен", "does not start", "won't start", "fuel", "pressure")):
        scored["fuel_pump"] = max(scored.get("fuel_pump", 0), 65)

    return [
        PartCandidate(PARTS[key], confidence, reasons.get(key, "Вероятная неисправная деталь."))
        for key, confidence in sorted(scored.items(), key=lambda item: item[1], reverse=True)
    ]


def should_offer_parts(candidates: list[PartCandidate]) -> bool:
    return bool(candidates and candidates[0].confidence >= 60 and candidates[0].part.key != "unknown")


def format_candidates(candidates: list[PartCandidate], limit: int = 3, language_code: str = "") -> str:
    if not candidates:
        return ""
    english = (language_code or "").lower().startswith("en")
    lines = ["Likely parts:" if english else "Вероятные детали:"]
    for candidate in candidates[:limit]:
        name = candidate.part.name_en if english else candidate.part.name_ru
        lines.append(f"* {name} ({candidate.confidence}%)")
    return "\n".join(lines)
