from services.i18n import is_english


DEMO_MENU_TEXT = """Demo mode

Это безопасная витрина MVP: сценарии не вызывают OpenAI, Google или реальные API.

Выберите сценарий, чтобы быстро показать ценность продукта."""

DEMO_MENU_TEXT_EN = """Demo mode

This is a safe MVP showcase: scenarios do not call OpenAI, Google, or real APIs.

Choose a scenario to quickly show the product value."""

DEMO_SCENARIOS = {
    "🎬 Demo: диагностика": """Demo: диагностика → запчасть

Пользователь:
Машину трясет на холостых.

Бот:
1. Уточняет, проблема появилась внезапно или постепенно.
2. Учитывает авто из гаража или просит VIN/модель.
3. Показывает вероятные причины:
   - катушка зажигания 70%
   - свеча зажигания 20%
   - форсунка 10%
4. Предлагает подобрать подходящую запчасть.

Ценность:
Бот ведет пользователя от симптома к конкретному действию, а не просто отвечает советом.""",
    "🎬 Demo: safety": """Demo: safety triage

Пользователь:
Пропали тормоза, педаль мягкая.

Бот:
1. Определяет критический риск.
2. Не предлагает DIY.
3. Говорит не продолжать движение.
4. Предлагает эвакуатор или срочную помощь рядом.

Ценность:
Продукт снижает риск опасных решений и создает доверие.""",
    "🎬 Demo: сервис": """Demo: правильный сервис

Пользователь:
Мне нужен официальный дилерский центр.

Бот:
1. Не ищет обычные СТО.
2. Выбирает категорию "Дилерский центр".
3. Просит геолокацию или адрес.
4. Показывает контакты, карту и маршрут.

Ценность:
Бот понимает намерение и ведет к нужному типу сервиса.""",
    "🎬 Demo: запчасти": """Demo: parts intelligence

Пользователь:
Нужна катушка зажигания на Toyota Camry 2019.

Бот:
1. Определяет авто и деталь.
2. Спрашивает бюджет.
3. Показывает:
   - оригинал OEM
   - качественный аналог
   - дешевый аналог с предупреждением
4. Дает короткие кликабельные ссылки для поиска.

Ценность:
Это мост между диагностикой, покупкой детали и ремонтом.""",
    "🎬 Demo: summary": """MVP summary

AutoBot сейчас показывает основу AI Automotive Care Platform:

1. Диагностика по симптомам.
2. Оценка риска движения.
3. Гараж и VIN-контекст.
4. Подбор запчастей.
5. Поиск нужного типа сервиса.
6. DIY-сопровождение.
7. История и напоминания.

Что усиливается после финансирования:
TecDoc / parts API, booking, payments, mobile app, fleet dashboard, dealer network, insurance/fleet B2B.""",
}

DEMO_SCENARIOS_EN = {
    "🎬 Demo: diagnosis": """Demo: diagnosis → part

User:
The car shakes at idle.

Bot:
1. Asks whether the problem appeared suddenly or gradually.
2. Uses the garage car or asks for VIN/model.
3. Shows likely causes:
   - ignition coil 70%
   - spark plug 20%
   - injector 10%
4. Offers to find the suitable part.

Value:
The bot guides the user from symptom to concrete action, instead of just giving generic advice.""",
    "🎬 Demo: safety": """Demo: safety triage

User:
The brakes disappeared, pedal is soft.

Bot:
1. Detects critical risk.
2. Does not offer DIY repair.
3. Tells the user not to continue driving.
4. Offers tow truck or urgent help nearby.

Value:
The product reduces dangerous decisions and builds trust.""",
    "🎬 Demo: service": """Demo: right service

User:
I need an official dealer center.

Bot:
1. Does not search regular repair shops.
2. Selects the Dealer center category.
3. Asks for location or address.
4. Shows contacts, map, and route.

Value:
The bot understands intent and leads to the correct service type.""",
    "🎬 Demo: parts": """Demo: parts intelligence

User:
Need an ignition coil for Toyota Camry 2019.

Bot:
1. Detects vehicle and part.
2. Asks for budget.
3. Shows:
   - OEM original
   - quality aftermarket
   - budget aftermarket with warning
4. Gives short clickable search links.

Value:
This bridges diagnosis, part purchase, and repair.""",
    "🎬 Demo: summary": """MVP summary

AutoBot already demonstrates the base of an AI Automotive Care Platform:

1. Symptom-based diagnostics.
2. Driving risk triage.
3. Garage and VIN context.
4. Parts matching.
5. Correct service category search.
6. DIY guidance.
7. History and reminders.

What becomes stronger after funding:
TecDoc / parts API, booking, payments, mobile app, fleet dashboard, dealer network, insurance/fleet B2B.""",
}


def demo_menu_text(language_code: str = "") -> str:
    return DEMO_MENU_TEXT_EN if is_english(language_code) else DEMO_MENU_TEXT


def demo_labels(language_code: str = "") -> list[str]:
    return list(DEMO_SCENARIOS_EN.keys()) if is_english(language_code) else list(DEMO_SCENARIOS.keys())


def all_demo_labels() -> list[str]:
    return list(DEMO_SCENARIOS.keys()) + list(DEMO_SCENARIOS_EN.keys())


def get_demo_text(label: str, language_code: str = "") -> str:
    scenarios = DEMO_SCENARIOS_EN if is_english(language_code) else DEMO_SCENARIOS
    return scenarios.get(label) or DEMO_SCENARIOS.get(label) or DEMO_SCENARIOS_EN.get(label) or demo_menu_text(language_code)
