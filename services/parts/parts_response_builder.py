from services.parts.budget_filter import PartsRecommendation
from services.parts.oem_lookup import PartOption
from services.parts.search_query_builder import build_search_links
from services.parts.vin_parts_service import VehicleContext
from services.i18n import is_english
from utils import escape_markdown


CLASS_LABELS = {
    "original_oem": "OEM оригинал",
    "trusted_aftermarket": "качественный аналог",
    "cheap_aftermarket": "бюджетный аналог",
    "unknown": "неизвестный вариант",
}

CLASS_LABELS_EN = {
    "original_oem": "OEM original",
    "trusted_aftermarket": "quality aftermarket",
    "cheap_aftermarket": "budget aftermarket",
    "unknown": "unknown option",
}


def _money(value: int) -> str:
    return f"{value:,}".replace(",", " ") + " ₸"


def _format_option(option: PartOption, prefix: str, language_code: str = "") -> str:
    labels = CLASS_LABELS_EN if is_english(language_code) else CLASS_LABELS
    class_label = labels.get(option.classification, option.classification)
    title = f"{option.brand} - {class_label}"
    number_label = "Part number" if is_english(language_code) else "Номер"
    price_label = "Mock price" if is_english(language_code) else "Цена mock"
    return (
        f"*{escape_markdown(prefix)}*: {escape_markdown(title)}\n"
        f"{number_label}: `{escape_markdown(option.part_number)}`\n"
        f"{price_label}: *{escape_markdown(_money(option.price_kzt))}*"
    )


def build_parts_response(vehicle: VehicleContext, recommendation: PartsRecommendation, language_code: str = "") -> str:
    option = recommendation.recommended
    if is_english(language_code):
        lines = [
            f"*Parts match for {escape_markdown(vehicle.display_name or vehicle.make)}*",
            "",
            f"Part: *{escape_markdown(option.part_name_en)}*",
            f"Russian name: {escape_markdown(option.part_name_ru)}",
            "",
            "1. What to buy",
            _format_option(option, "Recommended", language_code),
        ]
        if recommendation.budget_note:
            lines.append("\nBudget: OEM original is above budget, so the main option is a quality aftermarket part.")
        if recommendation.warning:
            lines.append("\nImportant: A budget aftermarket part may have lower lifespan, weaker warranty, or less stable quality.")

        alternatives = recommendation.alternatives[:2]
        if alternatives:
            lines.append("\n2. Other options")
            for alt in alternatives:
                lines.append(_format_option(alt, "Option", language_code))

        lines.append("\n3. Where to search")
        for link in build_search_links(vehicle, option, language_code):
            lines.append(f"- [{escape_markdown(link.title)}]({link.url})")
        lines.append("\nBefore buying, verify the part number with VIN and the seller.")
        return "\n".join(lines)

    lines = [
        f"*Подбор запчасти для {escape_markdown(vehicle.display_name or vehicle.make)}*",
        "",
        f"Деталь: *{escape_markdown(option.part_name_ru)}*",
        f"По-английски: {escape_markdown(option.part_name_en)}",
        "",
        "1. Что покупать",
        _format_option(option, "Рекомендую", language_code),
    ]
    if recommendation.budget_note:
        lines.append(f"\nБюджет: {escape_markdown(recommendation.budget_note)}")
    if recommendation.warning:
        lines.append(f"\nВажно: {escape_markdown(recommendation.warning)}")

    alternatives = recommendation.alternatives[:2]
    if alternatives:
        lines.append("\n2. Другие варианты")
        for alt in alternatives:
            lines.append(_format_option(alt, "Вариант", language_code))

    lines.append("\n3. Где искать")
    for link in build_search_links(vehicle, option, language_code):
        lines.append(f"- [{escape_markdown(link.title)}]({link.url})")
    lines.append("\nПеред покупкой сверяйте номер детали с VIN и продавцом.")
    return "\n".join(lines)
