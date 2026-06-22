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
    waiting_for_vehicle = State()
    
    # Помощь
    helping = State()
    diy_mode = State()
    
    # Локация
    waiting_for_location = State()
