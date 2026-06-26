from database import get_api_usage_summary

def _money(value: float) -> str:
    return f"${value:.6f}"

async def format_api_stats() -> str:
    rows = await get_api_usage_summary()
    if not rows:
        return "API-статистика пока пустая."

    lines = ["API-статистика:"]
    total_cost = 0.0
    for row in rows:
        (
            provider,
            operation,
            calls,
            successes,
            failures,
            attempts,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            estimated_cost_usd,
        ) = row
        cost = estimated_cost_usd or 0.0
        total_cost += cost
        lines.append(
            f"{provider}/{operation}: вызовы {calls}, успешно {successes or 0}, "
            f"ошибки {failures or 0}, попытки {attempts or 0}, "
            f"токены {total_tokens or 0}, стоимость {_money(cost)}"
        )

    lines.append(f"Итого примерная стоимость: {_money(total_cost)}")
    return "\n".join(lines)
