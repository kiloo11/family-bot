"""
На сайте фото бывает двух видов (см. app/photos.py для стороны бота):
- обычный Telegram file_id — показываем через прокси /media/tg/<file_id>,
  который сам сходит в Bot API и отдаст картинку
- "web:<filename>" — фото загружено через сайт, лежит в UPLOADS_DIR,
  отдаём напрямую как статику /media/uploads/<filename>
"""
import os
import uuid
from typing import Optional

from fastapi import UploadFile

from app.config import UPLOADS_DIR

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def photo_url(photo_id: str) -> Optional[str]:
    if not photo_id:
        return None
    if photo_id.startswith("web:"):
        return f"/media/uploads/{photo_id[len('web:'):]}"
    return f"/media/tg/{photo_id}"


async def save_upload(file: UploadFile) -> str:
    """Сохраняет загруженный файл на диск, возвращает photo_id вида 'web:<filename>'."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(UPLOADS_DIR, filename)
    content = await file.read()
    with open(dest, "wb") as f:
        f.write(content)
    return f"web:{filename}"
