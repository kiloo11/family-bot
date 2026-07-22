import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
FAMILY_CHAT_ID = os.getenv("FAMILY_CHAT_ID") or None
DB_PATH = os.getenv("DB_PATH", "./data/family.db")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Amsterdam")
REMINDER_DAYS_BEFORE = int(os.getenv("REMINDER_DAYS_BEFORE", "3"))
REMINDER_HOUR = int(os.getenv("REMINDER_HOUR", "9"))

# Фото, загруженные через сайт (не через бота), лежат тут — рядом с базой,
# в той же volume, поэтому доступны и боту, и веб-сервису.
UPLOADS_DIR = os.getenv("UPLOADS_DIR", os.path.join(os.path.dirname(DB_PATH) or ".", "uploads"))
os.makedirs(UPLOADS_DIR, exist_ok=True)

# --- настройки веб-сайта (используются только web-сервисом, но лежат тут же,
#     чтобы всё окружение читалось из одного .env) ---
WEB_SECRET_KEY = os.getenv("WEB_SECRET_KEY", "")
WEB_PORT = int(os.getenv("WEB_PORT", "8000"))
# Если список пуст — залогиниться и увидеть данные семьи сможет любой, кто нажмёт
# "Войти через Telegram". Если хочешь ограничить сайт только своей семьёй —
# впиши telegram user id через запятую (свой ID можно узнать у @userinfobot).
ALLOWED_TG_IDS = {
    int(x) for x in os.getenv("ALLOWED_TG_IDS", "").split(",") if x.strip().isdigit()
}

# --- Telegram Login (OIDC) — новая схема входа через @BotFather → Bot Settings → Web Login ---
# Client ID совпадает с числовой частью BOT_TOKEN до двоеточия, но можно переопределить,
# если BotFather вдруг показал другое значение.
TELEGRAM_CLIENT_ID = os.getenv("TELEGRAM_CLIENT_ID") or BOT_TOKEN.split(":")[0]
TELEGRAM_CLIENT_SECRET = os.getenv("TELEGRAM_CLIENT_SECRET", "")
# Должен ТОЧНО совпадать (включая слэш на конце или его отсутствие) с одним из
# "Redirect URIs", зарегистрированных в BotFather → Login Widget.
TELEGRAM_REDIRECT_URI = os.getenv("TELEGRAM_REDIRECT_URI", "")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан. Заполни .env (см. .env.example).")
