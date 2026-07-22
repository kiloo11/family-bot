from datetime import date, timedelta

from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto

from app.db import (
    list_items, get_item, set_status, claim_item, delete_item, roll_recurring_bill,
    list_album_photos, count_album_photos, set_rating, list_history_items,
)
from app.keyboards import (
    category_menu, item_actions, album_actions, CATEGORY_TITLES,
    watched_movie_actions, rating_choice, wishlist_history_actions,
)
from app.photos import to_photo_input

router = Router()


async def edit_text_or_caption(callback: CallbackQuery, new_text: str, reply_markup=None):
    """Карточки желаний с фото редактируются через caption, остальные — через text."""
    if callback.message.photo:
        await callback.message.edit_caption(caption=new_text, reply_markup=reply_markup)
    else:
        await callback.message.edit_text(new_text, reply_markup=reply_markup)


def current_text(callback: CallbackQuery) -> str:
    return callback.message.caption if callback.message.photo else callback.message.text


def format_item(row) -> str:
    if row["category"] == "wishlist":
        parts = [f"🎁 {row['title']}"]
        if row["description"]:
            parts.append(row["description"])
        if row["price"]:
            parts.append(f"💵 {row['price']}")
        if row["url"]:
            parts.append(row["url"])
        parts.append(f"— добавил(а) {row['added_by_name']}")
        if row["status"] == "claimed":
            who = f": {row['claimed_by_name']}" if row["claimed_by_name"] else ""
            parts.append(f"🙋 Забронировано{who}")
        elif row["status"] == "done":
            parts.append("✅ Выполнено")
        return "\n".join(parts)

    if row["category"] == "movie":
        parts = [f"🎬 {row['title']}"]
        if row["description"]:
            parts.append(row["description"])
        parts.append(f"— предложил(а) {row['added_by_name']}")
        if row["rating"]:
            parts.append("⭐" * row["rating"])
        return "\n".join(parts)

    if row["category"] == "bill":
        parts = [f"💰 {row['title']}"]
        if row["price"]:
            parts.append(f"Сумма: {row['price']}")
        if row["due_date"]:
            parts.append(f"Срок: {row['due_date']}")
        if row["is_recurring"]:
            parts.append("🔁 повторяющийся")
        return "\n".join(parts)

    if row["category"] == "album":
        parts = [f"📷 {row['title']}"]
        if row["location"]:
            parts.append(f"📍 {row['location']}")
        if row["due_date"]:
            parts.append(f"📅 {row['due_date']}")
        parts.append(f"— добавил(а) {row['added_by_name']}")
        return "\n".join(parts)

    return row["title"]


@router.callback_query(F.data.startswith("list:"))
async def show_list(callback: CallbackQuery):
    category = callback.data.split(":", 1)[1]
    rows = list_items(category, status="active")
    title = CATEGORY_TITLES.get(category, category)

    if not rows:
        await callback.message.edit_text(
            f"{title}\n\nПока пусто. Добавь что-нибудь!",
            reply_markup=category_menu(category),
        )
        await callback.answer()
        return

    await callback.message.edit_text(f"{title}\n\nСписок ниже 👇", reply_markup=category_menu(category))
    for row in rows:
        caption = format_item(row)
        if category == "album":
            photo_count = count_album_photos(row["id"])
            await callback.message.answer(
                caption,
                reply_markup=album_actions(row["id"], photo_count),
            )
        elif category == "wishlist" and row["photo_id"]:
            await callback.message.answer_photo(
                to_photo_input(row["photo_id"]),
                caption=caption,
                reply_markup=item_actions(row["id"], category),
            )
        else:
            await callback.message.answer(
                caption,
                reply_markup=item_actions(row["id"], category),
            )
    await callback.answer()


@router.callback_query(F.data == "watched:movie")
async def show_watched_movies(callback: CallbackQuery):
    rows = list_items("movie", status="done")
    if not rows:
        await callback.answer("Ещё ничего не отмечено просмотренным", show_alert=True)
        return

    await callback.message.answer("✅ Просмотренные фильмы 👇")
    for row in rows:
        await callback.message.answer(format_item(row), reply_markup=watched_movie_actions(row["id"]))
    await callback.answer()


@router.callback_query(F.data == "history:wishlist")
async def show_wishlist_history(callback: CallbackQuery):
    rows = list_history_items("wishlist")
    if not rows:
        await callback.answer("В истории пока пусто", show_alert=True)
        return

    await callback.message.answer("🗂 История желаний (выполненные и забронированные) 👇")
    for row in rows:
        caption = format_item(row)
        if row["photo_id"]:
            await callback.message.answer_photo(
                to_photo_input(row["photo_id"]),
                caption=caption,
                reply_markup=wishlist_history_actions(row["id"]),
            )
        else:
            await callback.message.answer(caption, reply_markup=wishlist_history_actions(row["id"]))
    await callback.answer()


@router.callback_query(F.data.startswith("restore:"))
async def restore_item(callback: CallbackQuery):
    item_id = int(callback.data.split(":", 1)[1])
    set_status(item_id, "active")
    await edit_text_or_caption(callback, "↩️ Возвращено в активные: " + (current_text(callback) or ""))
    await callback.answer("Возвращено")


@router.callback_query(F.data.startswith("viewalbum:"))
async def view_album(callback: CallbackQuery):
    item_id = int(callback.data.split(":", 1)[1])
    photos = list_album_photos(item_id)
    if not photos:
        await callback.answer("В альбоме пока нет фото", show_alert=True)
        return

    # Telegram позволяет не больше 10 фото в одной медиагруппе — режем на пачки
    chunk = 10
    for i in range(0, len(photos), chunk):
        batch = photos[i:i + chunk]
        media = [InputMediaPhoto(media=to_photo_input(p["photo_id"])) for p in batch]
        await callback.message.answer_media_group(media)
    await callback.answer()


@router.callback_query(F.data.startswith("done:"))
async def mark_done(callback: CallbackQuery):
    item_id = int(callback.data.split(":", 1)[1])
    row = get_item(item_id)
    if row and row["category"] == "bill" and row["is_recurring"]:
        # переносим на следующий месяц вместо закрытия
        old_due = date.fromisoformat(row["due_date"])
        year = old_due.year + (1 if old_due.month == 12 else 0)
        month = 1 if old_due.month == 12 else old_due.month + 1
        day = min(old_due.day, 28)
        new_due = date(year, month, day).isoformat()
        roll_recurring_bill(item_id, new_due)
        await edit_text_or_caption(callback, f"✅ Оплачено! Следующий срок: {new_due}")
    else:
        set_status(item_id, "done")
        await edit_text_or_caption(callback, "✅ Готово: " + (current_text(callback) or ""))
        if row and row["category"] == "movie":
            await callback.message.answer(
                f"Как тебе «{row['title']}»? Оцени:",
                reply_markup=rating_choice(item_id),
            )
    await callback.answer("Отмечено")


@router.callback_query(F.data.startswith("rateopen:"))
async def rate_open(callback: CallbackQuery):
    item_id = int(callback.data.split(":", 1)[1])
    row = get_item(item_id)
    title = row["title"] if row else ""
    await callback.message.answer(f"Оцени «{title}»:", reply_markup=rating_choice(item_id))
    await callback.answer()


@router.callback_query(F.data.startswith("rate:"))
async def rate_movie(callback: CallbackQuery):
    _, item_id_str, rating_str = callback.data.split(":")
    item_id, rating = int(item_id_str), int(rating_str)
    set_rating(item_id, rating)
    await callback.message.edit_text(f"Оценка сохранена: {'⭐' * rating}")
    await callback.answer("Спасибо!")


@router.callback_query(F.data.startswith("claim:"))
async def claim(callback: CallbackQuery):
    item_id = int(callback.data.split(":", 1)[1])
    claim_item(item_id, callback.from_user.full_name)
    await edit_text_or_caption(
        callback,
        (current_text(callback) or "") + f"\n\n🙋 Забронировал(а): {callback.from_user.full_name}",
    )
    await callback.answer("Забронировано")


@router.callback_query(F.data.startswith("del:"))
async def delete(callback: CallbackQuery):
    item_id = int(callback.data.split(":", 1)[1])
    delete_item(item_id)
    await edit_text_or_caption(callback, "🗑 Удалено")
    await callback.answer()
