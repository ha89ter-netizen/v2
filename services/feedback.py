from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards import response_feedback_keyboard


async def ask_response_feedback(
    message: Message,
    state: FSMContext,
    question: str,
    response_type: str,
    problem: str,
    vehicle: str = "",
) -> None:
    feedback_message = await message.answer(question, reply_markup=response_feedback_keyboard())
    data = await state.get_data()
    contexts = data.get("feedback_contexts", {})
    contexts[str(feedback_message.message_id)] = {
        "response_type": response_type,
        "problem": problem,
        "vehicle": vehicle,
    }
    if len(contexts) > 20:
        oldest_keys = list(contexts.keys())[:-20]
        for key in oldest_keys:
            contexts.pop(key, None)
    await state.update_data(feedback_contexts=contexts)
