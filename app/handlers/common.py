from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message

from app.db import upsert_user
from app.keyboards import category_menu, bottom_menu, CATEGORY_TITLES, TITLE_TO_CATEGORY

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    upsert_user(message.from_user.id, message.from_user.full_name)
    await message.answer(
        "Привет! Это семейный органайзер 👨‍👩‍👧‍👦\n\n"
        "Выбирай раздел кнопками внизу 👇",
        reply_markup=bottom_menu(),
    )


@router.message(StateFilter(None), F.text.in_(TITLE_TO_CATEGORY.keys()))
async def open_category_from_bottom_button(message: Message):
    category = TITLE_TO_CATEGORY[message.text]
    title = CATEGORY_TITLES[category]
    await message.answer(f"{title}\n\nЧто делаем?", reply_markup=category_menu(category))
