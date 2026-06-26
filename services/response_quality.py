from utils import normalize_text_key


PRACTICAL_WORDS = {
    "проверь",
    "проверьте",
    "осмотрите",
    "измерьте",
    "остановитесь",
    "замените",
    "сервис",
    "диагност",
    "шаг",
}


def improve_ai_answer(answer: str, answer_type: str) -> str:
    text = (answer or "").strip()
    if not text:
        return (
            "Не смог подготовить нормальный ответ. Опишите симптом подробнее: "
            "когда появился, что горит на панели, есть ли звук, запах или течь."
        )

    key = normalize_text_key(text)
    has_practical_step = any(word in key for word in PRACTICAL_WORDS)
    too_short = len(key.split()) < 18

    if not too_short and has_practical_step:
        return text

    additions = []
    if too_short:
        additions.append(
            "Уточните, когда появляется симптом: на холодную, при разгоне, торможении или на холостых."
        )
    if not has_practical_step:
        additions.append(
            "Практический минимум: проверьте уровень жидкостей, ошибки на панели, запах, течи и посторонние звуки."
        )
    if answer_type in {"diagnosis", "diy_instructions", "photo_analysis"}:
        additions.append(
            "Если есть дым, запах топлива, отказ тормозов, перегрев или потеря управления — не продолжайте движение."
        )

    return f"{text}\n\n" + "\n".join(additions)
