import base64
import logging
from openai import AsyncOpenAI
from config import config
from database import (
    get_cached_response,
    has_negative_feedback,
    record_api_usage,
    save_cached_response,
)
from services.common_answers import get_common_initial_advice
from services.i18n import is_english
from services.intent import detect_local_intent
from services.response_quality import improve_ai_answer
from services.retry import retry_async

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

def _token_usage(response) -> tuple[int, int, int]:
    usage = getattr(response, "usage", None)
    if not usage:
        return 0, 0, 0
    prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
    completion_tokens = getattr(usage, "completion_tokens", 0) or 0
    total_tokens = getattr(usage, "total_tokens", prompt_tokens + completion_tokens) or 0
    return prompt_tokens, completion_tokens, total_tokens

def _estimated_openai_cost(prompt_tokens: int, completion_tokens: int) -> float:
    input_cost = prompt_tokens * config.OPENAI_INPUT_COST_PER_1M / 1_000_000
    output_cost = completion_tokens * config.OPENAI_OUTPUT_COST_PER_1M / 1_000_000
    return input_cost + output_cost

async def _chat_completion(
    operation: str,
    max_tokens: int,
    messages: list[dict],
    model: str = "",
) -> str:
    attempts = 1
    model_name = model or config.OPENAI_MODEL
    try:
        async def action():
            return await client.chat.completions.create(
                model=model_name,
                max_tokens=max_tokens,
                messages=messages,
            )

        response, attempts = await retry_async(action, config.OPENAI_MAX_RETRIES)
        prompt_tokens, completion_tokens, total_tokens = _token_usage(response)
        await record_api_usage(
            provider="openai",
            operation=operation,
            model=model_name,
            success=True,
            attempts=attempts,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=_estimated_openai_cost(prompt_tokens, completion_tokens),
        )
        return response.choices[0].message.content
    except Exception as e:
        await record_api_usage(
            provider="openai",
            operation=operation,
            model=model_name,
            success=False,
            attempts=attempts,
            error=str(e),
        )
        raise

SYSTEM_PROMPT = """Ты AutoBot — профессиональный автомобильный ассистент в Telegram.

СТИЛЬ ОБЩЕНИЯ:
- Вежливо и дружелюбно
- Конкретно, без воды, но не поверхностно
- Для диагностики используй структуру и объясняй логику
- Максимум 260 слов за раз
- Один вопрос за раз

ЯЗЫК:
- Отвечай на том же языке на котором пишет пользователь

ЛОГИКА:
- Серьёзная проблема (тормоза, рулевое, дым) → сразу говори что опасно и нужен специалист
- Не ставь окончательный диагноз без проверки
- Давай вероятности, простые проверки, риск и следующий шаг
- Если нужна замена детали, назови наиболее вероятную деталь"""

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
    local_intent = detect_local_intent(message)
    if local_intent:
        await record_api_usage("local_intent", "detect_intent", success=True)
        return local_intent

    try:
        answer = await _chat_completion(
            operation="detect_intent",
            max_tokens=10,
            messages=[
                {"role": "system", "content": INTENT_PROMPT},
                {"role": "user", "content": message}
            ]
        )
        intent = answer.strip().lower()
        valid = ["find_service", "diy_repair", "diagnose", "garage", "location", "question"]
        return intent if intent in valid else "question"
    except Exception as e:
        logger.error(f"Intent ошибка: {e}")
        return "question"

def _cache_key(text: str, language_code: str = "") -> str:
    prefix = "[deep-v2]"
    return f"{prefix} [en] {text}" if is_english(language_code) else f"{prefix} {text}"


async def get_initial_advice(problem: str, language_code: str = "") -> str:
    common_answer = None if is_english(language_code) else get_common_initial_advice(problem)
    cache_problem = _cache_key(problem, language_code)
    if common_answer and not await has_negative_feedback("initial_advice", cache_problem):
        await record_api_usage("local_answers", "initial_advice", success=True)
        return common_answer

    cached = await get_cached_response("initial_advice", cache_problem)
    if cached:
        await record_api_usage("openai_cache", "initial_advice", success=True)
        return cached

    try:
        user_prompt = (
            f"Car problem: {problem}\n\nGive a diagnostic card in English, not a generic answer. Use this structure:\n1. Most likely causes with percentages\n2. Why these causes fit the symptoms\n3. Simple checks the driver can do safely\n4. Driving risk: can drive / drive only shortly / do not drive\n5. Most likely part if replacement is needed\n6. One next question if more data is needed"
            if is_english(language_code)
            else f"Проблема с авто: {problem}\n\nДай диагностическую карточку, а не общий совет. Структура:\n1. Самые вероятные причины с процентами\n2. Почему эти причины подходят под симптомы\n3. Простые безопасные проверки\n4. Риск движения: можно ехать / только недалеко / нельзя ехать\n5. Вероятная деталь под замену, если она нужна\n6. Один следующий вопрос, если данных мало"
        )
        answer = await _chat_completion(
            operation="initial_advice",
            max_tokens=650,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )
        answer = improve_ai_answer(answer, "initial_advice")
        await save_cached_response("initial_advice", cache_problem, answer)
        return answer
    except Exception as e:
        logger.error(f"OpenAI ошибка: {e}")
        return "Could not get advice, please try again." if is_english(language_code) else "Не смог получить совет, попробуй ещё раз."

async def get_diagnosis(problem: str, vehicle: str, language_code: str = "") -> str:
    cache_problem = _cache_key(problem, language_code)
    cached = await get_cached_response("diagnosis", cache_problem, vehicle)
    if cached:
        await record_api_usage("openai_cache", "diagnosis", success=True)
        return cached

    try:
        user_prompt = (
            f"Vehicle: {vehicle}\nProblem: {problem}\n\nGive a deep vehicle-specific diagnostic card in English. Use this structure:\n1. Most likely causes with percentages\n2. Why these causes fit this exact vehicle and symptoms\n3. What to check first, second, third\n4. Driving risk and what happens if ignored\n5. Likely replacement part and confidence\n6. Best next action: continue diagnosis / find part / DIY / service"
            if is_english(language_code)
            else f"Авто: {vehicle}\nПроблема: {problem}\n\nДай глубокую диагностическую карточку под конкретное авто. Структура:\n1. Самые вероятные причины с процентами\n2. Почему эти причины подходят под это авто и симптомы\n3. Что проверить первым, вторым, третьим\n4. Риск движения и что будет, если игнорировать\n5. Вероятная деталь под замену и уверенность\n6. Лучший следующий шаг: продолжить диагностику / найти деталь / DIY / сервис"
        )
        answer = await _chat_completion(
            operation="diagnosis",
            max_tokens=750,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )
        answer = improve_ai_answer(answer, "diagnosis")
        await save_cached_response("diagnosis", cache_problem, answer, vehicle)
        return answer
    except Exception as e:
        logger.error(f"OpenAI ошибка: {e}")
        return "Could not get a diagnosis, please try again." if is_english(language_code) else "Не смог получить диагноз, попробуй ещё раз."

async def get_diy_instructions(problem: str, vehicle: str, language_code: str = "") -> str:
    cache_problem = _cache_key(problem, language_code)
    cached = await get_cached_response("diy_instructions", cache_problem, vehicle)
    if cached:
        await record_api_usage("openai_cache", "diy_instructions", success=True)
        return cached

    try:
        user_prompt = (
            f"Vehicle: {vehicle}\nProblem: {problem}\n\nGive step-by-step DIY repair instructions in English. Include: 1. Safety stop conditions 2. Tools needed 3. Diagnosis checks before replacing parts 4. Clear steps 5. Common mistakes 6. When to stop and go to service. End by asking if it worked."
            if is_english(language_code)
            else f"Авто: {vehicle}\nПроблема: {problem}\n\nДай пошаговую DIY-инструкцию. Укажи:\n1. Когда нельзя продолжать из-за безопасности\n2. Инструменты\n3. Проверки до замены деталей\n4. Чёткие шаги\n5. Частые ошибки\n6. Когда остановиться и ехать в сервис\n\nВ конце спроси, получилось ли."
        )
        answer = await _chat_completion(
            operation="diy_instructions",
            max_tokens=600,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )
        answer = improve_ai_answer(answer, "diy_instructions")
        await save_cached_response("diy_instructions", cache_problem, answer, vehicle)
        return answer
    except Exception as e:
        logger.error(f"OpenAI ошибка: {e}")
        return "Could not get instructions, please try again." if is_english(language_code) else "Не смог получить инструкцию, попробуй ещё раз."

async def continue_conversation(
    user_message: str,
    problem: str,
    vehicle: str,
    history: list,
    language_code: str = "",
) -> tuple[str, list]:
    history = history + [{"role": "user", "content": user_message}]

    try:
        reply = await _chat_completion(
            operation="continue_conversation",
            max_tokens=400,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT + ("\n\nIMPORTANT: Answer in English." if is_english(language_code) else ""),
                }
            ] + history
        )
        history = history + [{"role": "assistant", "content": reply}]

        if len(history) > 10:
            history = history[-10:]

        return reply, history
    except Exception as e:
        logger.error(f"OpenAI ошибка: {e}")
        return ("Connection error, please try again." if is_english(language_code) else "Ошибка соединения, попробуйте ещё раз."), history

async def analyze_photo(image_bytes: bytes, caption: str = "", photo_context: str = "", language_code: str = "") -> str:
    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    if is_english(language_code):
        user_text = (
            "Analyze the photo as an automotive assistant. "
            "Identify what is visible, the possible issue, risk level, and next steps. "
            "Format the answer in short blocks: What is visible, Risk, What to do now, When to go to service. "
            "If the photo is not enough, say what needs to be clarified. "
            "Do not make a final diagnosis from the photo alone. "
            "If you see smoke, fuel leak, heavy oil/coolant leak, wheel, brake, or electrical damage, warn about danger.\n\n"
            f"Photo type: {photo_context or 'not specified'}\n"
            f"User comment: {caption or 'none'}"
        )
    else:
        user_text = (
            "Проанализируй фото как автомобильный ассистент. "
            "Определи, что видно на фото, возможную проблему, уровень риска и следующие шаги. "
            "Ответ оформи коротко блоками: Что видно, Риск, Что сделать сейчас, Когда ехать в сервис. "
            "Если по фото нельзя сделать вывод, честно скажи что нужно уточнить. "
            "Не ставь окончательный диагноз только по фото. "
            "Если видны дым, течь топлива, сильная течь масла/антифриза, повреждение колеса, тормозов или электрики — предупреди об опасности.\n\n"
            f"Тип фото: {photo_context or 'не указан'}\n"
            f"Комментарий пользователя: {caption or 'нет'}"
        )
    try:
        answer = await _chat_completion(
            operation="photo_analysis",
            max_tokens=500,
            model=config.OPENAI_VISION_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT + ("\n\nIMPORTANT: Answer in English." if is_english(language_code) else "")},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}",
                                "detail": "low",
                            },
                        },
                    ],
                },
            ],
        )
        return improve_ai_answer(answer, "photo_analysis")
    except Exception as e:
        logger.error(f"OpenAI photo ошибка: {e}")
        return "Could not analyze the photo, please send the image again." if is_english(language_code) else "Не смог проанализировать фото, попробуйте отправить снимок ещё раз."
