import sqlite3
from contextlib import contextmanager
from datetime import date
from typing import Optional

from app.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    tg_id INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,          -- wishlist | movie | bill | album
    title TEXT NOT NULL,
    description TEXT,
    price TEXT,
    url TEXT,
    photo_id TEXT,                   -- Telegram file_id фото, только для wishlist
    location TEXT,                   -- страна/город, только для album
    due_date TEXT,                   -- ISO date; для bill — срок оплаты, для album — дата поездки
    is_recurring INTEGER DEFAULT 0,  -- только для bill
    status TEXT DEFAULT 'active',    -- active | done | claimed
    rating INTEGER,                  -- оценка 1-5, только для просмотренных фильмов
    added_by_id INTEGER,
    added_by_name TEXT,
    claimed_by_name TEXT,            -- кто "забронировал" подарок (скрыто от именинника вручную)
    reminded_on TEXT,                -- дата последнего отправленного напоминания
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS album_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,        -- ссылка на items.id (альбом)
    photo_id TEXT NOT NULL,          -- Telegram file_id
    added_by_name TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        # миграции для баз, созданных до появления новых полей
        for stmt in (
            "ALTER TABLE items ADD COLUMN photo_id TEXT",
            "ALTER TABLE items ADD COLUMN location TEXT",
            "ALTER TABLE items ADD COLUMN rating INTEGER",
        ):
            try:
                conn.execute(stmt)
            except sqlite3.OperationalError:
                pass  # колонка уже есть


def upsert_user(tg_id: int, name: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO users (tg_id, name) VALUES (?, ?) "
            "ON CONFLICT(tg_id) DO UPDATE SET name=excluded.name",
            (tg_id, name),
        )


def add_item(category: str, title: str, added_by_id: int, added_by_name: str,
             description: str = "", price: str = "", url: str = "",
             photo_id: Optional[str] = None, location: Optional[str] = None,
             due_date: Optional[str] = None, is_recurring: bool = False) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO items
               (category, title, description, price, url, photo_id, location, due_date,
                is_recurring, added_by_id, added_by_name)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (category, title, description, price, url, photo_id, location, due_date,
             int(is_recurring), added_by_id, added_by_name),
        )
        return cur.lastrowid


def list_items(category: str, status: str = "active"):
    with get_conn() as conn:
        if status == "all":
            rows = conn.execute(
                "SELECT * FROM items WHERE category=? ORDER BY "
                "CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date, created_at",
                (category,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM items WHERE category=? AND status=? ORDER BY "
                "CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date, created_at",
                (category, status),
            ).fetchall()
        return rows


def get_item(item_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()


def set_status(item_id: int, status: str):
    with get_conn() as conn:
        conn.execute("UPDATE items SET status=? WHERE id=?", (status, item_id))


def list_history_items(category: str):
    """Всё, что ушло из активного списка: и выполненное, и забронированное."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM items WHERE category=? AND status IN ('done', 'claimed') "
            "ORDER BY created_at DESC",
            (category,),
        ).fetchall()


def claim_item(item_id: int, claimed_by_name: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE items SET status='claimed', claimed_by_name=? WHERE id=?",
            (claimed_by_name, item_id),
        )


def set_rating(item_id: int, rating: int):
    with get_conn() as conn:
        conn.execute("UPDATE items SET rating=? WHERE id=?", (rating, item_id))


def delete_item(item_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM items WHERE id=?", (item_id,))
        conn.execute("DELETE FROM album_photos WHERE item_id=?", (item_id,))


def bills_due_soon(cutoff_date: str):
    """Оплаты, чей срок наступает не позже cutoff_date и ещё не оплаченные."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM items WHERE category='bill' AND status='active' "
            "AND due_date IS NOT NULL AND due_date <= ? "
            "AND (reminded_on IS NULL OR reminded_on != ?)",
            (cutoff_date, date.today().isoformat()),
        ).fetchall()


def mark_reminded(item_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE items SET reminded_on=? WHERE id=?",
            (date.today().isoformat(), item_id),
        )


def roll_recurring_bill(item_id: int, new_due_date: str):
    """После оплаты повторяющегося платежа — переносим срок на следующий период."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE items SET due_date=?, status='active', reminded_on=NULL WHERE id=?",
            (new_due_date, item_id),
        )


# ---------- фотоальбомы ----------

def add_album_photo(item_id: int, photo_id: str, added_by_name: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO album_photos (item_id, photo_id, added_by_name) VALUES (?, ?, ?)",
            (item_id, photo_id, added_by_name),
        )


def list_album_photos(item_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM album_photos WHERE item_id=? ORDER BY id", (item_id,)
        ).fetchall()


def count_album_photos(item_id: int) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM album_photos WHERE item_id=?", (item_id,)
        ).fetchone()
        return row["c"] if row else 0


def get_album_photo(photo_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM album_photos WHERE id=?", (photo_id,)).fetchone()


def delete_album_photo(photo_id: int):
    """Удаляет одно фото из альбома (не весь альбом). photo_id — это id строки в
    album_photos, а не Telegram file_id."""
    with get_conn() as conn:
        conn.execute("DELETE FROM album_photos WHERE id=?", (photo_id,))
