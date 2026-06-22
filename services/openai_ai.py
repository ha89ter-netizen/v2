import logging
from openai import AsyncOpenAI
from config import config

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

SYSTEM_PROMPT = """Ты AutoBot — профессиональный автомобильный ассистент в Telegram.

СТИЛЬ ОБЩЕНИЯ:
- Вежливо и дружелюбно
- Коротко и конкретно, без воды
- Максимум 150 слов за раз
- Один вопрос за раз

ЯЗЫК:
- Отвечай на том же языке на котором пишет пользователь

ЛОГИКА:
- Серьёзная проблема (тормоза, рулевое, дым) → сразу говори что опасно и нужен специалист
- Средняя проблема → уточни есть ли опыт
- Лёгкая проблема → сразу давай решение"""

INTENT_PROMPT = """Ты определяешь намерение пользователя в автомобильном боте.

Верни ТОЛЬКО одно слово из списка:
- find_service — хочет найти СТО, шиномонтаж, сервис, запчасти
- diy_repair — хочет починить сам, нужна инструкция
- diagnose — описывает проблему с авто, хочет диагноз
- garage — хочет добавить машину, открыть гараж
- location — хочет обновить или сохранить локацию
- question — просто вопрос по авто

Отвечай ТОЛЬКО одним словом без точек и пробелов."""

async def detect_intent(message: str) -> str:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=10,
            messages=[
                {"role": "system", "content": INTENT_PROMPT},
                {"role": "user", "content": message}
            ]
        )
        intent = response.choices[0].message.content.strip().lower()
        valid = ["find_service", "diy_repair", "diagnose", "garage", "location", "question"]
        return intent if intent in valid else "question"
    except Exception as e:
        logger.error(f"Intent ошибка: {e}")
        return "question"

async def get_initial_advice(problem: str) -> str:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=300,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Проблема с авто: {problem}\n\nДай краткий первичный совет — 2-3 предложения. Скажи что это может быть и насколько серьёзно. Не задавай вопросов."}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI ошибка: {e}")
        return "Не смог получить совет, попробуй ещё раз."

async def get_diagnosis(problem: str, vehicle: str) -> str:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=300,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Авто: {vehicle}\nПроблема: {problem}\n\nДай точный диагноз под эту модель. 3-4 предложения. В конце спроси — будет чинить сам или найти сервис?"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI ошибка: {e}")
        return "Не смог получить диагноз, попробуй ещё раз."

async def get_diy_instructions(problem: str, vehicle: str) -> str:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=600,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Авто: {vehicle}\nПроблема: {problem}\n\nДай пошаговую инструкцию как починить самому. Укажи:\n1. Инструменты которые нужны\n2. Чёткие шаги\n3. На что обратить внимание\n\nВ конце спроси получилось ли."}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI ошибка: {e}")
        return "Не смог получить инструкцию, попробуй ещё раз."

async def continue_conversation(
    user_message: str,
    problem: str,
    vehicle: str,
    history: list,
) -> tuple[str, list]:
    history = history + [{"role": "user", "content": user_message}]

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=400,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history
        )
        reply = response.choices[0].message.content
        history = history + [{"role": "assistant", "content": reply}]

        if len(history) > 10:
            history = history[-10:]

        return reply, history
    except Exception as e:
        logger.error(f"OpenAI ошибка: {e}")
        return "Ошибка соединения, попробуйте ещё раз.", history

