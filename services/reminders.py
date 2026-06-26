from datetime import datetime
from typing import Optional


def parse_reminder_text(text: str) -> tuple[str, str, Optional[int], Optional[int], Optional[int]]:
    value = text.strip()
    due_date = ""
    due_mileage = None
    recurring_interval_days = None
    recurring_interval_km = None

    if "|" not in value:
        return value, due_date, due_mileage, recurring_interval_days, recurring_interval_km

    parts = [part.strip() for part in value.split("|")]
    title = parts[0]
    for part in parts[1:]:
        if not part:
            continue
        normalized = part.lower()
        is_recurring = normalized.startswith("каждые ") or normalized.startswith("каждый ")
        clean_part = normalized.replace("каждые", "", 1).replace("каждый", "", 1).strip() if is_recurring else normalized

        if clean_part.endswith("км"):
            raw = clean_part[:-2].strip().replace(" ", "")
            if raw.isdigit():
                if is_recurring:
                    recurring_interval_km = int(raw)
                else:
                    due_mileage = int(raw)
            continue
        if is_recurring and any(word in clean_part for word in ["день", "дня", "дней"]):
            raw = clean_part.split()[0] if clean_part.split() else ""
            if raw.isdigit():
                recurring_interval_days = int(raw)
            continue
        try:
            datetime.strptime(part, "%Y-%m-%d")
            due_date = part
        except ValueError:
            title = f"{title} {part}".strip()

    return title, due_date, due_mileage, recurring_interval_days, recurring_interval_km


def format_reminders(reminders: list) -> str:
    if not reminders:
        return (
            "Активных напоминаний пока нет.\n\n"
            "Добавить: /add_reminder\n"
            "Формат: Замена масла | 2026-08-01 | 120000 км | каждые 8000 км"
        )

    lines = ["Ваши напоминания:"]
    for row in reminders:
        reminder_id, title, due_date, due_mileage, status, created_at, *repeat = row
        recurring_days = repeat[0] if len(repeat) > 0 else None
        recurring_km = repeat[1] if len(repeat) > 1 else None
        details = []
        if due_date:
            details.append(f"дата {due_date}")
        if due_mileage:
            details.append(f"пробег {due_mileage} км")
        if recurring_days:
            details.append(f"повтор каждые {recurring_days} дней")
        if recurring_km:
            details.append(f"повтор каждые {recurring_km} км")
        detail_text = f" ({', '.join(details)})" if details else ""
        lines.append(f"{reminder_id}. {title}{detail_text}")
    lines.append("\nЗакрыть напоминание: /done_reminder ID")
    return "\n".join(lines)


def format_api_errors(errors: list) -> str:
    if not errors:
        return "API-ошибок пока нет."

    lines = ["Последние API-ошибки:"]
    for provider, operation, model, attempts, error, created_at in errors:
        model_text = f" / {model}" if model else ""
        lines.append(
            f"{created_at} — {provider}/{operation}{model_text}, "
            f"попытки {attempts}: {error or 'без текста ошибки'}"
        )
    return "\n".join(lines)
