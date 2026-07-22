"""
Авторизация на сайте через "Log In with Telegram" — актуальную (2026) OIDC-схему.

Telegram отказался от старого iframe-виджета с /setdomain в пользу стандартного
OpenID Connect: Authorization Code Flow + PKCE. Схема такая:

1. Пользователь жмёт "Войти через Telegram" -> GET /auth/telegram/login.
   Мы генерируем code_verifier/code_challenge (PKCE) и state (защита от CSRF),
   кладём их в короткоживущую подписанную cookie и редиректим на oauth.telegram.org.
2. Пользователь подтверждает вход в Telegram, тот редиректит обратно на наш
   TELEGRAM_REDIRECT_URI с ?code=...&state=...
3. Мы меняем code на id_token на сервере (POST /token с Client ID + Client Secret,
   Client Secret никогда не уходит в браузер).
4. id_token — подписанный JWT. Проверяем подпись через JWKS Telegram, issuer, audience
   и срок действия, и только после этого верим данным пользователя внутри токена.
5. Выдаём свою сессионную cookie (как и раньше — подписанную, но уже нашим секретом).

Официальная документация: https://core.telegram.org/bots/telegram-login
"""
import asyncio
import base64
import hashlib
import secrets
from typing import Optional
from urllib.parse import urlencode

import httpx
import jwt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.config import (
    WEB_SECRET_KEY, ALLOWED_TG_IDS,
    TELEGRAM_CLIENT_ID, TELEGRAM_CLIENT_SECRET, TELEGRAM_REDIRECT_URI,
)

SESSION_COOKIE = "family_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 дней

OAUTH_STATE_COOKIE = "tg_oauth_state"
OAUTH_STATE_MAX_AGE = 600  # 10 минут на завершение логина

AUTH_ENDPOINT = "https://oauth.telegram.org/auth"
TOKEN_ENDPOINT = "https://oauth.telegram.org/token"
JWKS_URL = "https://oauth.telegram.org/.well-known/jwks.json"
ISSUER = "https://oauth.telegram.org"

if not WEB_SECRET_KEY:
    raise RuntimeError(
        "WEB_SECRET_KEY не задан. Впиши в .env любую длинную случайную строку "
        "(например: python3 -c \"import secrets; print(secrets.token_hex(32))\")."
    )
if not TELEGRAM_CLIENT_SECRET:
    raise RuntimeError(
        "TELEGRAM_CLIENT_SECRET не задан. Возьми его в @BotFather → выбери бота → "
        "Bot Settings → Web Login (там же рядом Client ID и Redirect URIs)."
    )
if not TELEGRAM_REDIRECT_URI:
    raise RuntimeError(
        "TELEGRAM_REDIRECT_URI не задан. Должен ТОЧНО совпадать с одним из "
        "Redirect URI, зарегистрированных в @BotFather → Bot Settings → Web Login "
        "(включая слэш на конце, если он там есть)."
    )

_session_serializer = URLSafeTimedSerializer(WEB_SECRET_KEY, salt="family-bot-session")
_oauth_state_serializer = URLSafeTimedSerializer(WEB_SECRET_KEY, salt="family-bot-oauth-state")

_jwks_client = jwt.PyJWKClient(JWKS_URL)


# ---------- сессия сайта (после успешного логина) ----------

def create_session_token(user: dict) -> str:
    return _session_serializer.dumps(user)


def read_session_token(token: str) -> Optional[dict]:
    try:
        return _session_serializer.loads(token, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None


# ---------- шаг 1: запуск OIDC-логина (PKCE) ----------

def build_authorize_url() -> tuple[str, str]:
    """Возвращает (url для редиректа на Telegram, значение cookie с state+code_verifier)."""
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    state = secrets.token_urlsafe(24)

    params = {
        "client_id": TELEGRAM_CLIENT_ID,
        "redirect_uri": TELEGRAM_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid profile",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    url = f"{AUTH_ENDPOINT}?{urlencode(params)}"
    cookie_value = _oauth_state_serializer.dumps({"state": state, "code_verifier": code_verifier})
    return url, cookie_value


def read_oauth_state_cookie(token: str) -> Optional[dict]:
    try:
        return _oauth_state_serializer.loads(token, max_age=OAUTH_STATE_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None


# ---------- шаг 2: обмен code -> id_token, проверка подписи ----------

async def exchange_code_for_user(code: str, code_verifier: str) -> Optional[dict]:
    """Меняет authorization code на id_token и возвращает проверенные данные пользователя,
    либо None, если что-то пошло не так (истёкший код, подделанный токен и т.д.)."""
    basic = base64.b64encode(f"{TELEGRAM_CLIENT_ID}:{TELEGRAM_CLIENT_SECRET}".encode()).decode()

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            TOKEN_ENDPOINT,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": TELEGRAM_REDIRECT_URI,
                "client_id": TELEGRAM_CLIENT_ID,
                "code_verifier": code_verifier,
            },
            headers={
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
    if resp.status_code != 200:
        return None

    id_token = resp.json().get("id_token")
    if not id_token:
        return None

    return await _verify_id_token(id_token)


async def _verify_id_token(id_token: str) -> Optional[dict]:
    try:
        # получение и подбор ключа по kid — блокирующий HTTP-запрос, уводим в отдельный поток
        signing_key = await asyncio.to_thread(_jwks_client.get_signing_key_from_jwt, id_token)
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256", "ES256", "EdDSA", "ES256K"],
            audience=str(TELEGRAM_CLIENT_ID),
            issuer=ISSUER,
        )
    except Exception:
        return None

    raw_id = claims.get("id") or claims.get("sub")
    if raw_id is None:
        return None
    tg_id = int(raw_id)

    if ALLOWED_TG_IDS and tg_id not in ALLOWED_TG_IDS:
        return None

    return {
        "tg_id": tg_id,
        "first_name": claims.get("given_name") or claims.get("name") or "",
        "last_name": claims.get("family_name", ""),
        "username": claims.get("preferred_username", ""),
        "photo_url": claims.get("picture", ""),
    }
