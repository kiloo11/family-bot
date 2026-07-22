from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot

from app.config import FAMILY_CHAT_ID, TIMEZONE, REMINDER_DAYS_BEFORE, REMINDER_HOUR
from app.db import bills_due_soon, mark_reminded


async def check_bills(bot: Bot):
    cutoff = (date.today() + timedelta(days=REMINDER_DAYS_BEFORE)).isoformat()
    rows = bills_due_soon(cutoff)
    for row in rows:
        days_left = (date.fromisoformat(row["due_date"]) - date.today()).days
        if days_left < 0:
            when = f"⚠️ Просрочено ({row['due_date']})"
        elif days_left == 0:
            when = "сегодня"
        else:
            when = f"через {days_left} дн. ({row['due_date']})"

        text = f"💰 Напоминание об оплате\n\n{row['title']}\nСрок: {when}"
        if row["price"]:
            text += f"\nСумма: {row['price']}"

        chat_id = FAMILY_CHAT_ID or row["added_by_id"]
        try:
            await bot.send_message(chat_id, text)
        except Exception:
            pass
        mark_reminded(row["id"])


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        check_bills,
        trigger=CronTrigger(hour=REMINDER_HOUR, minute=0),
        args=[bot],
        id="check_bills",
        replace_existing=True,
    )
    return scheduler
