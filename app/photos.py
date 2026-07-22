"""
photo_id в базе бывает двух видов:
- обычный Telegram file_id (фото прислали боту)
- "web:<filename>" — фото загрузили через сайт, физически лежит в UPLOADS_DIR

Это единственное место, которое знает про такое различие на стороне бота.
"""
import os

from aiogram.types import FSInputFile

from app.config import UPLOADS_DIR


def to_photo_input(photo_id: str):
    if photo_id and photo_id.startswith("web:"):
        filename = photo_id[len("web:"):]
        return FSInputFile(os.path.join(UPLOADS_DIR, filename))
    return photo_id
