from aiogram.fsm.state import State, StatesGroup

class UserFlow(StatesGroup):
    # Главное меню
    main_menu = State()
    
    # Гараж
    garage = State()
    adding_vin = State()
    adding_brand = State()
    
    # Проблема
    waiting_for_problem = State()
    waiting_for_problem_onset = State()
    waiting_for_diagnostic_details = State()
    waiting_for_vehicle = State()
    
    # Помощь
    helping = State()
    diy_mode = State()
    
    # Локация
    waiting_for_location = State()

    # Фото
    waiting_for_photo_context = State()
    waiting_for_photo = State()

    # Напоминания
    waiting_for_reminder = State()

    # Запчасти
    waiting_for_part_name = State()
    waiting_for_part_budget = State()
    waiting_for_part_vehicle = State()
