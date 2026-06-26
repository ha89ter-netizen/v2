from config import config


def is_admin(user_id: int) -> bool:
    return bool(config.ADMIN_IDS) and user_id in config.ADMIN_IDS


def admin_denied_text() -> str:
    if not config.ADMIN_IDS:
        return "Админка выключена: ADMIN_IDS не задан в .env."
    return "Эта команда доступна только администратору."
