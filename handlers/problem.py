from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states import UserFlow
from keyboards import vin_skip_keyboard, fix_choice_keyboard
from services.openai_ai import get_initial_advice, get_diagnosis

router = Router()

@router.message(F.text == "🔧 Описать проблему")
async def btn_describe_problem(message: Message, state: FSMContext):
    await state.set_state(UserFlow.waiting_for_problem)
    await message.answer("Опишите проблему с автомобилем своими словами 👇")

@router.message(F.text == "📍 Найти сервис рядом")
async def btn_find_service(message: Message, state: FSMContext):
    await state.update_data(problem="поиск ближайшего сервиса")
    await state.set_state(UserFlow.waiting_for_location)
    from keyboards import location_keyboard
    await message.answer(
        "Отправьте геолокацию или введите адрес 👇",
        reply_markup=location_keyboard(),
    )

@router.message(UserFlow.waiting_for_problem, F.text)
async def receive_problem(message: Message, state: FSMContext):
    problem = message.text.strip()

    if len(problem) < 5:
        await message.answer("Пожалуйста опишите проблему подробнее 🙏")
        return

    await state.update_data(problem=problem)
    await message.answer("Анализирую проблему...")
    advice = await get_initial_advice(problem)
    await message.answer(advice)

    data = await state.get_data()
    vehicle = data.get("vehicle")

    if vehicle:
        await state.set_state(UserFlow.helping)
        await message.answer("Уточняю диагноз для вашего автомобиля...")
        diagnosis = await get_diagnosis(problem, vehicle)
        await message.answer(diagnosis, reply_markup=fix_choice_keyboard())
    else:
        await state.set_state(UserFlow.waiting_for_vehicle)
        await message.answer(
            "Для точной диагностики введите VIN-код автомобиля 👇\n\n"
            "_17 символов, находится на лобовом стекле или в документах_",
            parse_mode="Markdown",
            reply_markup=vin_skip_keyboard(),
        )
