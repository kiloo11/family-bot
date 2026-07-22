from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

CATEGORY_TITLES = {
    "wishlist": "🎁 Желания",
    "movie": "🎬 Фильмы",
    "bill": "💰 Оплаты",
    "album": "📷 Альбомы",
}

# Обратный маппинг: текст кнопки -> ключ категории (для reply-клавиатуры внизу экрана)
TITLE_TO_CATEGORY = {v: k for k, v in CATEGORY_TITLES.items()}


def bottom_menu() -> ReplyKeyboardMarkup:
    """Единственное меню навигации — постоянные кнопки под окном ввода сообщения.
    Инлайн-дублей этих же разделов больше нет, чтобы не плодить кнопки в чате."""
    b = ReplyKeyboardBuilder()
    for title in CATEGORY_TITLES.values():
        b.button(text=title)
    b.adjust(2, 2)
    return b.as_markup(resize_keyboard=True, is_persistent=True)


def category_menu(category: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="➕ Добавить", callback_data=f"add:{category}")
    b.button(text="📋 Список", callback_data=f"list:{category}")
    if category == "movie":
        b.button(text="✅ Просмотрено", callback_data="watched:movie")
        b.adjust(2, 1)
    elif category == "wishlist":
        b.button(text="🗂 История", callback_data="history:wishlist")
        b.adjust(2, 1)
    else:
        b.adjust(2)
    return b.as_markup()


def item_actions(item_id: int, category: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if category == "wishlist":
        b.button(text="🙋 Забронировать", callback_data=f"claim:{item_id}")
    b.button(text="✅ Готово", callback_data=f"done:{item_id}")
    b.button(text="🗑 Удалить", callback_data=f"del:{item_id}")
    b.adjust(1)
    return b.as_markup()


def watched_movie_actions(item_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⭐ Оценить", callback_data=f"rateopen:{item_id}")
    b.button(text="🗑 Удалить", callback_data=f"del:{item_id}")
    b.adjust(1)
    return b.as_markup()


def wishlist_history_actions(item_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="↩️ Вернуть в активные", callback_data=f"restore:{item_id}")
    b.button(text="🗑 Удалить", callback_data=f"del:{item_id}")
    b.adjust(1)
    return b.as_markup()


def rating_choice(item_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for n in range(1, 6):
        b.button(text="⭐" * n, callback_data=f"rate:{item_id}:{n}")
    b.adjust(5)
    return b.as_markup()


def album_actions(item_id: int, photo_count: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if photo_count:
        b.button(text=f"🖼 Смотреть фото ({photo_count})", callback_data=f"viewalbum:{item_id}")
    b.button(text="➕ Добавить фото", callback_data=f"addphoto:{item_id}")
    b.button(text="🗑 Удалить альбом", callback_data=f"del:{item_id}")
    b.adjust(1)
    return b.as_markup()


def album_photos_done() -> InlineKeyboardMarkup:
    """Показывается, пока пользователь присылает фото в альбом — жмёт, когда закончил."""
    b = InlineKeyboardBuilder()
    b.button(text="✅ Готово, сохранить", callback_data="album_done")
    return b.as_markup()


def recurring_choice() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔁 Повторяющийся", callback_data="rec:yes")
    b.button(text="1️⃣ Разовый", callback_data="rec:no")
    b.adjust(2)
    return b.as_markup()
