import os
from datetime import date, timedelta
from typing import Optional
from urllib.parse import quote

import httpx
from fastapi import FastAPI, Request, Response, Depends, HTTPException, Form, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.config import BOT_TOKEN, UPLOADS_DIR
from app.db import (
    init_db, list_items, get_item, add_item, set_status, claim_item, delete_item,
    roll_recurring_bill, add_album_photo, list_album_photos, count_album_photos, set_rating,
    get_album_photo, delete_album_photo, list_history_items,
)
from web.auth import (
    build_authorize_url, read_oauth_state_cookie, exchange_code_for_user,
    create_session_token, read_session_token, SESSION_COOKIE,
    OAUTH_STATE_COOKIE,
)
from web.photos import photo_url, save_upload

init_db()

# Собранный React-фронтенд (web/frontend, см. README) — Vite кладёт сюда index.html
# и хэшированные assets/*, ссылки на них уже прописаны внутри index.html.
DIST_DIR = os.path.join(os.path.dirname(__file__), "static", "dist")
os.makedirs(DIST_DIR, exist_ok=True)  # чтобы StaticFiles не падал на старте до первой сборки фронтенда

app = FastAPI(title="Семейный органайзер")
app.mount("/static/dist", StaticFiles(directory=DIST_DIR), name="dist")
app.mount("/media/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

_tg_file_cache: dict[str, str] = {}  # file_id -> file_path (кэш на время жизни процесса)


# ---------- авторизация (Telegram Login / OIDC) ----------

def get_current_user(request: Request) -> dict:
    token = request.cookies.get(SESSION_COOKIE)
    user = read_session_token(token) if token else None
    if not user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    return user


@app.get("/auth/telegram/login")
async def auth_telegram_login():
    """Шаг 1: генерируем PKCE-пару и state, редиректим на Telegram."""
    url, state_cookie_value = build_authorize_url()
    response = RedirectResponse(url)
    response.set_cookie(OAUTH_STATE_COOKIE, state_cookie_value, httponly=True, samesite="lax", max_age=600)
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie(SESSION_COOKIE)
    return response


# ---------- страницы ----------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, code: Optional[str] = None, state: Optional[str] = None,
                 error: Optional[str] = None):
    # Redirect_uri у Telegram зарегистрирован как корень сайта, поэтому колбэк OIDC
    # (?code=...&state=...) прилетает сюда же, на "/", а не на отдельный /callback.
    # Фронтенд — React SPA (web/frontend): состояние логина она узнаёт через GET /api/me,
    # а ошибку входа показывает по query-параметру ?auth_error=..., в который мы редиректим.
    if error:
        return RedirectResponse(url=f"/?auth_error={quote(f'Telegram вернул ошибку: {error}')}")

    if code and state:
        saved = read_oauth_state_cookie(request.cookies.get(OAUTH_STATE_COOKIE, ""))
        if not saved or saved.get("state") != state:
            response = RedirectResponse(url=f"/?auth_error={quote('Сессия входа истекла, попробуй ещё раз')}")
            response.delete_cookie(OAUTH_STATE_COOKIE)
            return response
        user = await exchange_code_for_user(code, saved["code_verifier"])
        if not user:
            response = RedirectResponse(url=f"/?auth_error={quote('Не удалось подтвердить вход через Telegram')}")
            response.delete_cookie(OAUTH_STATE_COOKIE)
            return response
        token = create_session_token(user)
        response = RedirectResponse(url="/")
        response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30)
        response.delete_cookie(OAUTH_STATE_COOKIE)
        return response

    return FileResponse(os.path.join(DIST_DIR, "index.html"))


@app.get("/api/me")
async def api_me(user: dict = Depends(get_current_user)):
    return user


# ---------- фото ----------

@app.get("/media/tg/{file_id}")
async def media_telegram_photo(file_id: str):
    """Прокси картинок, присланных боту в Telegram: сайт не хранит их сам,
    а на лету забирает у Bot API (file_path кэшируется в памяти процесса)."""
    file_path = _tg_file_cache.get(file_id)
    async with httpx.AsyncClient() as client:
        if not file_path:
            r = await client.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile", params={"file_id": file_id})
            data = r.json()
            if not data.get("ok"):
                raise HTTPException(status_code=404, detail="Фото не найдено")
            file_path = data["result"]["file_path"]
            _tg_file_cache[file_id] = file_path

        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        resp = await client.get(file_url)
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Фото не найдено")
        return StreamingResponse(iter([resp.content]), media_type="image/jpeg")


# ---------- API: списки ----------

def serialize_item(row) -> dict:
    d = dict(row)
    if d.get("photo_id"):
        d["photo_url"] = photo_url(d["photo_id"])
    if d.get("category") == "album":
        d["photo_count"] = count_album_photos(d["id"])
    return d


@app.get("/api/items/{category}")
async def api_list_items(category: str, status: str = "active", user: dict = Depends(get_current_user)):
    if status not in ("active", "done", "history"):
        raise HTTPException(status_code=400, detail="status должен быть active, done или history")
    if status == "history":
        rows = list_history_items(category)
    else:
        rows = list_items(category, status=status)
    return [serialize_item(r) for r in rows]


@app.post("/api/items/{item_id}/done")
async def api_mark_done(item_id: int, user: dict = Depends(get_current_user)):
    row = get_item(item_id)
    if not row:
        raise HTTPException(status_code=404)
    if row["category"] == "bill" and row["is_recurring"]:
        old_due = date.fromisoformat(row["due_date"])
        year = old_due.year + (1 if old_due.month == 12 else 0)
        month = 1 if old_due.month == 12 else old_due.month + 1
        day = min(old_due.day, 28)
        roll_recurring_bill(item_id, date(year, month, day).isoformat())
    else:
        set_status(item_id, "done")
    return {"ok": True}


@app.post("/api/items/{item_id}/claim")
async def api_claim(item_id: int, user: dict = Depends(get_current_user)):
    name = user["first_name"] or user["username"] or "Кто-то"
    claim_item(item_id, name)
    return {"ok": True}


@app.post("/api/items/{item_id}/restore")
async def api_restore(item_id: int, user: dict = Depends(get_current_user)):
    set_status(item_id, "active")
    return {"ok": True}


@app.post("/api/items/{item_id}/delete")
async def api_delete(item_id: int, user: dict = Depends(get_current_user)):
    delete_item(item_id)
    return {"ok": True}


@app.post("/api/items/{item_id}/rating")
async def api_set_rating(item_id: int, rating: int = Form(...), user: dict = Depends(get_current_user)):
    if not 1 <= rating <= 5:
        raise HTTPException(status_code=400, detail="Оценка должна быть от 1 до 5")
    set_rating(item_id, rating)
    return {"ok": True}


def _display_name(user: dict) -> str:
    return user["first_name"] or user["username"] or "Кто-то"


# ---------- API: добавление ----------

@app.post("/api/wishlist")
async def api_add_wishlist(
    title: str = Form(...), description: str = Form(""), price: str = Form(""),
    url: str = Form(""), photo: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user),
):
    photo_id = await save_upload(photo) if photo and photo.filename else None
    add_item(
        category="wishlist", title=title, added_by_id=user["tg_id"], added_by_name=_display_name(user),
        description=description, price=price, url=url, photo_id=photo_id,
    )
    return {"ok": True}


@app.post("/api/movies")
async def api_add_movie(
    title: str = Form(...), description: str = Form(""),
    user: dict = Depends(get_current_user),
):
    add_item(
        category="movie", title=title, added_by_id=user["tg_id"], added_by_name=_display_name(user),
        description=description,
    )
    return {"ok": True}


@app.post("/api/bills")
async def api_add_bill(
    title: str = Form(...), price: str = Form(""), due_date: str = Form(...),
    is_recurring: bool = Form(False), user: dict = Depends(get_current_user),
):
    try:
        date.fromisoformat(due_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Дата в формате ГГГГ-ММ-ДД")
    add_item(
        category="bill", title=title, added_by_id=user["tg_id"], added_by_name=_display_name(user),
        price=price, due_date=due_date, is_recurring=is_recurring,
    )
    return {"ok": True}


@app.post("/api/albums")
async def api_add_album(
    title: str = Form(...), due_date: str = Form(""), location: str = Form(""),
    user: dict = Depends(get_current_user),
):
    if due_date:
        try:
            date.fromisoformat(due_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Дата в формате ГГГГ-ММ-ДД")
    item_id = add_item(
        category="album", title=title, added_by_id=user["tg_id"], added_by_name=_display_name(user),
        due_date=due_date or None, location=location,
    )
    return {"ok": True, "item_id": item_id}


@app.get("/api/albums/{item_id}/photos")
async def api_album_photos(item_id: int, user: dict = Depends(get_current_user)):
    photos = list_album_photos(item_id)
    return [{"id": p["id"], "url": photo_url(p["photo_id"])} for p in photos]


@app.post("/api/albums/{item_id}/photos")
async def api_add_album_photos(
    item_id: int, files: list[UploadFile] = File(...),
    user: dict = Depends(get_current_user),
):
    if not get_item(item_id):
        raise HTTPException(status_code=404)
    for f in files:
        if not f.filename:
            continue
        photo_id = await save_upload(f)
        add_album_photo(item_id, photo_id, _display_name(user))
    return {"ok": True, "photo_count": count_album_photos(item_id)}


@app.post("/api/albums/{item_id}/photos/{photo_id}/delete")
async def api_delete_album_photo(item_id: int, photo_id: int, user: dict = Depends(get_current_user)):
    photo = get_album_photo(photo_id)
    if not photo or photo["item_id"] != item_id:
        raise HTTPException(status_code=404)
    delete_album_photo(photo_id)
    return {"ok": True, "photo_count": count_album_photos(item_id)}
