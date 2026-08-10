import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_PATH = os.getenv("DB_PATH", "diabet_bot.db")

# Telegram ID администраторов через запятую, например: ADMIN_IDS=123456789,987654321
ADMIN_IDS = [
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
]

if not BOT_TOKEN:
    # Не падаем при импорте (например, при тестировании), но предупреждаем.
    print("[config] ВНИМАНИЕ: переменная окружения BOT_TOKEN не задана. "
          "Создайте файл .env на основе .env и укажите токен бота.")
