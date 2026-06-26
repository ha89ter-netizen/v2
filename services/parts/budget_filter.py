from dataclasses import dataclass
from typing import Optional

from services.parts.oem_lookup import PartOption
from services.parts.parts_classifier import SAFETY_SYSTEMS, PartDefinition


BUDGET_LABELS = {
    "до 20 000 ₸": 20_000,
    "до 50 000 ₸": 50_000,
    "до 100 000 ₸": 100_000,
    "без ограничений": None,
    "up to 20 000 ₸": 20_000,
    "up to 50 000 ₸": 50_000,
    "up to 100 000 ₸": 100_000,
    "no limit": None,
}


@dataclass(frozen=True)
class PartsRecommendation:
    recommended: PartOption
    alternatives: list[PartOption]
    budget_limit: Optional[int]
    warning: str = ""
    budget_note: str = ""


def parse_budget(label: str) -> Optional[int]:
    return BUDGET_LABELS.get(label.strip().lower())


def _by_class(options: list[PartOption], classification: str) -> Optional[PartOption]:
    return next((option for option in options if option.classification == classification), None)


def choose_recommendation(options: list[PartOption], part: PartDefinition, budget_limit: Optional[int]) -> PartsRecommendation:
    if not options:
        unknown = PartOption(part.key, part.name_ru, part.name_en, "unknown", "-", "unknown", 0, "нет данных")
        return PartsRecommendation(unknown, [], budget_limit, warning="По этой детали пока нет данных в mock-каталоге.")

    safe_options = list(options)
    if part.system in SAFETY_SYSTEMS:
        safe_options = [option for option in safe_options if option.classification != "unknown"]
    if not safe_options:
        unknown = PartOption(part.key, part.name_ru, part.name_en, "unknown", "-", "unknown", 0, "нет безопасных данных")
        return PartsRecommendation(
            unknown,
            [],
            budget_limit,
            warning="Для этой safety-системы нет надёжных данных. Нельзя рекомендовать unknown как основной вариант.",
        )

    original = _by_class(safe_options, "original_oem")
    trusted = _by_class(safe_options, "trusted_aftermarket")
    cheap = _by_class(safe_options, "cheap_aftermarket")
    recommended = original or trusted or cheap or safe_options[0]
    budget_note = ""

    if budget_limit is not None:
        if original and original.price_kzt <= budget_limit:
            recommended = original
        elif original and trusted:
            recommended = trusted
            budget_note = "Оригинал выше бюджета, поэтому основной вариант — качественный аналог."
        elif trusted and trusted.price_kzt <= budget_limit:
            recommended = trusted
        elif cheap and cheap.price_kzt <= budget_limit:
            recommended = cheap
        elif trusted:
            recommended = trusted
            budget_note = "В бюджете нет безопасного варианта, лучше поднять бюджет до качественного аналога."

    warning = ""
    if recommended.classification == "cheap_aftermarket":
        warning = "Дешёвый аналог может иметь меньший ресурс, шум, слабую гарантию или нестабильное качество."
    if recommended.classification == "unknown":
        warning = "Неизвестный бренд нельзя считать надёжной рекомендацией."

    alternatives = [option for option in safe_options if option != recommended]
    return PartsRecommendation(recommended, alternatives, budget_limit, warning=warning, budget_note=budget_note)
