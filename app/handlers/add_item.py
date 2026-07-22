from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.db import add_item, upsert_user, add_album_photo, count_album_photos
from app.states import AddWishlist, AddMovie, AddBill, AddAlbum
from app.keyboards import category_menu, recurring_choice, album_photos_done, album_actions

router = Router()

SKIP = "skip"


# ---------- запуск диалога ----------

@router.callback_query(F.data.startswith("add:"))
async def start_add(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split(":", 1)[1]
    await state.update_data(category=category)

    if category == "wishlist":
        await state.set_state(AddWishlist.title)
        await callback.message.edit_text("Что хотим? Напиши название 🎁")
    elif category == "movie":
        await state.set_state(AddMovie.title)
        await callback.message.edit_text("Название фильма/сериала 🎬")
    elif category == "bill":
        await state.set_state(AddBill.title)
        await callback.message.edit_text("Название платежа (например: коммуналка) 💰")
    elif category == "album":
        await state.set_state(AddAlbum.title)
        await callback.message.edit_text("Название альбома (например: Поездка в Питер) 📷")
    await callback.answer()


# ---------- wishlist ----------

@router.message(AddWishlist.title)
async def wl_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AddWishlist.description)
    await message.answer("Комментарий/размер/цвет? (или напиши «-», если не нужно)")


@router.message(AddWishlist.description)
async def wl_description(message: Message, state: FSMContext):
    desc = "" if message.text.strip() == "-" else message.text
    await state.update_data(description=desc)
    await state.set_state(AddWishlist.price)
    await message.answer("Примерная цена? (или «-»)")


@router.message(AddWishlist.price)
async def wl_price(message: Message, state: FSMContext):
    price = "" if message.text.strip() == "-" else message.text
    await state.update_data(price=price)
    await state.set_state(AddWishlist.url)
    await message.answer("Ссылка на товар? (или «-»)")


@router.message(AddWishlist.url)
async def wl_url(message: Message, state: FSMContext):
    url = "" if message.text.strip() == "-" else message.text
    await state.update_data(url=url)
    await state.set_state(AddWishlist.photo)
    await message.answer("Пришли фото товара 📷 (или напиши «-», если фото не нужно)")


async def _save_wishlist_item(message: Message, state: FSMContext, photo_id: str | None):
    data = await state.get_data()
    upsert_user(message.from_user.id, message.from_user.full_name)
    add_item(
        category="wishlist",
        title=data["title"],
        added_by_id=message.from_user.id,
        added_by_name=message.from_user.full_name,
        description=data.get("description", ""),
        price=data.get("price", ""),
        url=data.get("url", ""),
        photo_id=photo_id,
    )
    await state.clear()
    await message.answer(
        f"Добавлено в желания: «{data['title']}» 🎁",
        reply_markup=category_menu("wishlist"),
    )


@router.message(AddWishlist.photo, F.photo)
async def wl_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id  # берём самое большое разрешение
    await _save_wishlist_item(message, state, photo_id)


@router.message(AddWishlist.photo, F.text)
async def wl_photo_skip(message: Message, state: FSMContext):
    if message.text.strip() != "-":
        await message.answer("Пришли фото 📷 или напиши «-», чтобы пропустить этот шаг")
        return
    await _save_wishlist_item(message, state, None)


# ---------- movie ----------

@router.message(AddMovie.title)
async def mv_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AddMovie.description)
    await message.answer("Комментарий (кто предложил, почему хотим посмотреть)? Или «-»")


@router.message(AddMovie.description)
async def mv_description(message: Message, state: FSMContext):
    desc = "" if message.text.strip() == "-" else message.text
    data = await state.get_data()
    upsert_user(message.from_user.id, message.from_user.full_name)
    add_item(
        category="movie",
        title=data["title"],
        added_by_id=message.from_user.id,
        added_by_name=message.from_user.full_name,
        description=desc,
    )
    await state.clear()
    await message.answer(
        f"Добавлено в список фильмов: «{data['title']}» 🎬",
        reply_markup=category_menu("movie"),
    )


# ---------- bill ----------

@router.message(AddBill.title)
async def bill_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AddBill.amount)
    await message.answer("Сумма? (например: 120€, или «-» если не важно)")


@router.message(AddBill.amount)
async def bill_amount(message: Message, state: FSMContext):
    amount = "" if message.text.strip() == "-" else message.text
    await state.update_data(price=amount)
    await state.set_state(AddBill.due_date)
    await message.answer("Срок оплаты в формате ГГГГ-ММ-ДД (например 2026-08-01)")


@router.message(AddBill.due_date)
async def bill_due_date(message: Message, state: FSMContext):
    text = message.text.strip()
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        await message.answer("Не похоже на дату. Формат: ГГГГ-ММ-ДД, например 2026-08-01")
        return
    await state.update_data(due_date=text)
    await state.set_state(AddBill.recurring)
    await message.answer("Это разовый платёж или повторяющийся (каждый месяц)?", reply_markup=recurring_choice())


@router.callback_query(AddBill.recurring, F.data.startswith("rec:"))
async def bill_recurring(callback: CallbackQuery, state: FSMContext):
    is_recurring = callback.data.endswith("yes")
    data = await state.get_data()
    upsert_user(callback.from_user.id, callback.from_user.full_name)
    add_item(
        category="bill",
        title=data["title"],
        added_by_id=callback.from_user.id,
        added_by_name=callback.from_user.full_name,
        price=data.get("price", ""),
        due_date=data["due_date"],
        is_recurring=is_recurring,
    )
    await state.clear()
    await callback.message.edit_text(
        f"Добавлен платёж «{data['title']}» на {data['due_date']} 💰",
        reply_markup=category_menu("bill"),
    )
    await callback.answer()


# ---------- album ----------

@router.message(AddAlbum.title)
async def al_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AddAlbum.date)
    await message.answer("Дата поездки в формате ГГГГ-ММ-ДД? (или «-», если не важно)")


@router.message(AddAlbum.date)
async def al_date(message: Message, state: FSMContext):
    text = message.text.strip()
    if text != "-":
        try:
            datetime.strptime(text, "%Y-%m-%d")
        except ValueError:
            await message.answer("Не похоже на дату. Формат: ГГГГ-ММ-ДД, например 2026-08-01, или «-»")
            return
    await state.update_data(due_date=None if text == "-" else text)
    await state.set_state(AddAlbum.location)
    await message.answer("Страна/город? (например: Италия, Рим — или «-»)")


@router.message(AddAlbum.location)
async def al_location(message: Message, state: FSMContext):
    location = "" if message.text.strip() == "-" else message.text
    data = await state.get_data()
    upsert_user(message.from_user.id, message.from_user.full_name)
    item_id = add_item(
        category="album",
        title=data["title"],
        added_by_id=message.from_user.id,
        added_by_name=message.from_user.full_name,
        due_date=data.get("due_date"),
        location=location,
    )
    await state.update_data(item_id=item_id)
    await state.set_state(AddAlbum.photos)
    await message.answer(
        "Альбом создан! Теперь присылай фото по одному 📷\n"
        "Когда закончишь — нажми «Готово».",
        reply_markup=album_photos_done(),
    )


@router.callback_query(F.data.startswith("addphoto:"))
async def start_add_photos(callback: CallbackQuery, state: FSMContext):
    """Добавить ещё фото в уже существующий альбом (запускается из списка альбомов)."""
    item_id = int(callback.data.split(":", 1)[1])
    await state.set_state(AddAlbum.photos)
    await state.update_data(item_id=item_id)
    await callback.message.answer(
        "Присылай фото по одному 📷 Когда закончишь — нажми «Готово».",
        reply_markup=album_photos_done(),
    )
    await callback.answer()


@router.message(AddAlbum.photos, F.photo)
async def al_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    item_id = data["item_id"]
    add_album_photo(item_id, message.photo[-1].file_id, message.from_user.full_name)
    total = count_album_photos(item_id)
    await message.answer(f"Добавлено 👍 Фото в альбоме: {total}", reply_markup=album_photos_done())


@router.message(AddAlbum.photos, F.text)
async def al_photo_wrong_input(message: Message):
    await message.answer("Пришли фото 📷 или нажми «Готово», чтобы завершить")


@router.callback_query(AddAlbum.photos, F.data == "album_done")
async def al_photos_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item_id = data["item_id"]
    total = count_album_photos(item_id)
    await state.clear()
    await callback.message.edit_text(
        f"Готово! В альбоме {total} фото 📷",
        reply_markup=album_actions(item_id, total),
    )
    await callback.answer()
