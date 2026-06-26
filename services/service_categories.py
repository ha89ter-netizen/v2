SERVICE_CATEGORIES = {
    "sto": {"type": "car_repair", "keywords": ["автосервис СТО", "car repair"], "label": "🔧 СТО", "label_en": "🔧 Repair shop", "radius": 7000},
    "dealer": {
        "type": "car_dealer",
        "keywords": [
            "официальный дилер",
            "дилерский центр",
            "официальный сервис",
            "dealer service center",
            "authorized car dealer",
        ],
        "label": "🏢 Дилерский центр",
        "label_en": "🏢 Dealer center",
        "radius": 15000,
        "min_rating": 3.5,
    },
    "diagnostics": {"type": "car_repair", "keywords": ["диагностика авто", "auto diagnostics"], "label": "🧰 Диагностика", "label_en": "🧰 Diagnostics", "radius": 7000},
    "tire": {"type": "car_repair", "keywords": ["шиномонтаж", "tire repair"], "label": "🛞 Шиномонтаж", "label_en": "🛞 Tire shop", "radius": 7000},
    "parts": {"type": "car_dealer", "keywords": ["автозапчасти", "auto parts"], "label": "🔩 Запчасти", "label_en": "🔩 Parts store", "radius": 9000},
    "electric": {"type": "car_repair", "keywords": ["автоэлектрик", "электрик авто", "car electrician"], "label": "⚡ Автоэлектрик", "label_en": "⚡ Auto electrician", "radius": 9000},
    "body": {"type": "car_repair", "keywords": ["кузовной ремонт", "малярка авто", "auto body repair"], "label": "🧱 Кузовной ремонт", "label_en": "🧱 Body repair", "radius": 10000},
    "alignment": {"type": "car_repair", "keywords": ["сход развал", "развал схождение", "wheel alignment"], "label": "📐 Сход-развал", "label_en": "📐 Wheel alignment", "radius": 8000},
    "glass": {"type": "car_repair", "keywords": ["автостекла", "замена лобового стекла", "auto glass"], "label": "🪟 Автостекла", "label_en": "🪟 Auto glass", "radius": 10000},
    "ac": {"type": "car_repair", "keywords": ["автокондиционер", "заправка кондиционера авто", "car air conditioning"], "label": "❄️ Кондиционер", "label_en": "❄️ A/C service", "radius": 10000},
    "salvage": {"type": "car_dealer", "keywords": ["авторазбор", "разбор авто", "used auto parts"], "label": "♻️ Авторазбор", "label_en": "♻️ Salvage yard", "radius": 12000, "min_rating": 3.5},
    "battery": {"type": "car_repair", "keywords": ["аккумулятор замена", "car battery"], "label": "🔋 АКБ", "label_en": "🔋 Battery", "radius": 9000},
    "gas": {"type": "gas_station", "keywords": ["АЗС заправка", "gas station"], "label": "⛽ Заправка", "label_en": "⛽ Gas station", "radius": 7000},
    "wash": {"type": "car_wash", "keywords": ["автомойка", "car wash"], "label": "🧽 Автомойка", "label_en": "🧽 Car wash", "radius": 7000},
    "detailing": {"type": "car_wash", "keywords": ["детейлинг авто", "auto detailing"], "label": "✨ Детейлинг", "label_en": "✨ Detailing", "radius": 9000},
    "oil": {"type": "car_repair", "keywords": ["замена масла", "oil change"], "label": "🛢 Замена масла", "label_en": "🛢 Oil change", "radius": 7000},
    "tow": {
        "type": "",
        "keywords": [
            "эвакуатор",
            "помощь на дороге",
            "tow truck",
            "roadside assistance",
        ],
        "label": "🚨 Срочная помощь",
        "label_en": "🚨 Tow truck",
        "radius": 12000,
        "min_rating": 0,
    },
}

SERVICE_BUTTON_ROWS = [
    ["🚨 Эвакуатор", "🔧 СТО"],
    ["🏢 Дилерский центр", "🧰 Диагностика"],
    ["🛞 Шиномонтаж", "🔩 Запчасти"],
    ["⚡ Автоэлектрик", "🧱 Кузовной ремонт"],
    ["📐 Сход-развал", "🪟 Автостекла"],
    ["❄️ Кондиционер", "♻️ Авторазбор"],
    ["🔋 АКБ", "⛽ Заправка"],
    ["🛢 Замена масла", "🧽 Автомойка"],
    ["✨ Детейлинг"],
]

SERVICE_BUTTON_ROWS_EN = [
    ["🚨 Tow truck", "🔧 Repair shop"],
    ["🏢 Dealer center", "🧰 Diagnostics"],
    ["🛞 Tire shop", "🔩 Parts store"],
    ["⚡ Auto electrician", "🧱 Body repair"],
    ["📐 Wheel alignment", "🪟 Auto glass"],
    ["❄️ A/C service", "♻️ Salvage yard"],
    ["🔋 Battery", "⛽ Gas station"],
    ["🛢 Oil change", "🧽 Car wash"],
    ["✨ Detailing"],
]

SERVICE_BUTTON_TO_CATEGORY = {
    "🚨 Эвакуатор": "tow",
    "🚨 Эвакуатор / срочная помощь": "tow",
    "🚨 Tow truck": "tow",
    "🚨 Emergency help": "tow",
}
SERVICE_BUTTON_TO_CATEGORY.update(
    {
        meta["label"]: key
        for key, meta in SERVICE_CATEGORIES.items()
        if key != "tow"
    }
)
SERVICE_BUTTON_TO_CATEGORY.update(
    {
        meta["label_en"]: key
        for key, meta in SERVICE_CATEGORIES.items()
        if key != "tow"
    }
)
