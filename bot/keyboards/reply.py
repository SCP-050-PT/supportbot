"""Обычные (reply) клавиатуры меню."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from bot.db.constants import STAFF_ROLES, Role

if TYPE_CHECKING:
    from bot.db import Database


class Btn:
    # Пользователь
    NEW_TICKET = "📝 Создать обращение"
    MY_TICKETS = "📂 Мои обращения"
    FAQ = "❓ Частые вопросы"
    CLOSE_TICKET = "✅ Закрыть обращение"
    CANCEL = "🚫 Отмена"
    # Сотрудники
    OPEN_TICKETS = "📥 Открытые обращения"
    CURRENT_TICKET = "📄 Текущее обращение"
    RELEASE = "🔓 Отпустить"
    STAFF_CLOSE = "🔒 Закрыть текущее"
    FIND_USER = "🔎 Найти пользователя"
    ADMIN_PANEL = "⚙️ Админ-панель"


def _kb(rows: list[list[str]]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t) for t in row] for row in rows],
        resize_keyboard=True,
    )


def user_menu(has_active: bool) -> ReplyKeyboardMarkup:
    first = Btn.CLOSE_TICKET if has_active else Btn.NEW_TICKET
    return _kb([[first], [Btn.MY_TICKETS, Btn.FAQ]])


def staff_menu(is_admin: bool) -> ReplyKeyboardMarkup:
    rows = [
        [Btn.OPEN_TICKETS, Btn.CURRENT_TICKET],
        [Btn.RELEASE, Btn.STAFF_CLOSE],
        [Btn.FIND_USER, Btn.FAQ],
    ]
    if is_admin:
        rows.append([Btn.ADMIN_PANEL])
    return _kb(rows)


def cancel_kb() -> ReplyKeyboardMarkup:
    return _kb([[Btn.CANCEL]])


async def menu_for(db_user: dict[str, Any], db: Database) -> ReplyKeyboardMarkup:
    role = db_user.get("role")
    if role in STAFF_ROLES:
        return staff_menu(role == Role.ADMIN)
    active = await db.tickets.get_active_by_user(db_user["_id"])
    return user_menu(active is not None)
