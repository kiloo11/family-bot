from aiogram.fsm.state import State, StatesGroup


class AddWishlist(StatesGroup):
    title = State()
    description = State()
    price = State()
    url = State()
    photo = State()


class AddMovie(StatesGroup):
    title = State()
    description = State()


class AddBill(StatesGroup):
    title = State()
    amount = State()
    due_date = State()
    recurring = State()


class AddAlbum(StatesGroup):
    title = State()
    date = State()
    location = State()
    photos = State()  # используется и при создании, и при доп. загрузке фото в существующий альбом
