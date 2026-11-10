"""Inline-клавиатуры."""
from __future__ import annotations

from typing import Any

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.db.constants import Role
from bot.keyboards.callbacks import CHECK_SUB, AdminCb, FaqCb, TicketCb, UserCb
from bot.texts import TIMER_NAMES
from bot.utils import is_muted


def _short(text: str, limit: int = 40) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


# ───── Обращения ─────

def accept_ticket_kb(ticket_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Принять", callback_data=TicketCb(action="accept", ticket_id=ticket_id))
    b.button(text="📜 История", callback_data=TicketCb(action="history", ticket_id=ticket_id))
    b.adjust(2)
    return b.as_markup()


def open_tickets_kb(tickets: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for t in tickets:
        b.button(
            text=_short(f"№{t['_id']} · {t.get('title', '')}"),
            callback_data=TicketCb(action="view", ticket_id=t["_id"]),
        )
    b.adjust(1)
    return b.as_markup()


# ───── FAQ ─────

def faq_list_kb(items: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for item in items:
        b.button(text=_short(item["question"]), callback_data=FaqCb(action="show", faq_id=str(item["_id"])))
    b.adjust(1)
    return b.as_markup()


def faq_back_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⬅️ К списку", callback_data=FaqCb(action="list"))
    return b.as_markup()


def faq_admin_kb(items: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for item in items:
        b.button(text="🗑 " + _short(item["question"], 36), callback_data=FaqCb(action="del", faq_id=str(item["_id"])))
    b.button(text="➕ Добавить вопрос", callback_data=AdminCb(action="faq_add"))
    b.button(text="⬅️ Назад", callback_data=AdminCb(action="home"))
    b.adjust(1)
    return b.as_markup()


# ───── Карточка пользователя ─────

def user_card_kb(target: dict[str, Any], viewer_is_admin: bool) -> InlineKeyboardMarkup:
    uid = target["_id"]
    role = target.get("role")
    b = InlineKeyboardBuilder()
    b.button(text="📂 Обращения", callback_data=UserCb(action="tickets", user_id=uid))
    if role == Role.USER:
        if is_muted(target):
            b.button(text="🔊 Снять мут", callback_data=UserCb(action="unmute", user_id=uid))
        else:
            b.button(text="🔇 Мут 1 ч", callback_data=UserCb(action="mute", user_id=uid, value=1))
            b.button(text="🔇 Мут 24 ч", callback_data=UserCb(action="mute", user_id=uid, value=24))
        if target.get("is_banned"):
            b.button(text="✅ Разбанить", callback_data=UserCb(action="unban", user_id=uid))
        else:
            b.button(text="⛔️ Забанить", callback_data=UserCb(action="ban", user_id=uid))
        if viewer_is_admin:
            b.button(text="⬆️ Сделать менеджером", callback_data=UserCb(action="promote", user_id=uid))
    elif role == Role.MANAGER and viewer_is_admin:
        b.button(text="⬇️ Снять роль менеджера", callback_data=UserCb(action="demote", user_id=uid))
    b.adjust(1, 2, 1, 1)
    return b.as_markup()


# ───── Админ-панель ─────

def admin_panel_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🧑‍💼 Менеджеры", callback_data=AdminCb(action="managers"))
    b.button(text="⏱ Таймеры", callback_data=AdminCb(action="timers"))
    b.button(text="👋 Приветствие", callback_data=AdminCb(action="start_msg"))
    b.button(text="📢 Подписка на канал", callback_data=AdminCb(action="channel"))
    b.button(text="❓ FAQ", callback_data=AdminCb(action="faq"))
    b.button(text="📣 Рассылка", callback_data=AdminCb(action="broadcast"))
    b.button(text="🧹 Очистить старые", callback_data=AdminCb(action="cleanup"))
    b.button(text="🔄 Обновить", callback_data=AdminCb(action="home"))
    b.adjust(2)
    return b.as_markup()


def back_kb(action: str = "home") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⬅️ Назад", callback_data=AdminCb(action=action))
    return b.as_markup()


def managers_kb(managers: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for m in managers:
        b.button(
            text="⬇️ " + _short(m.get("full_name") or str(m["_id"]), 34),
            callback_data=UserCb(action="demote", user_id=m["_id"], value=1),
        )
    b.button(text="⬅️ Назад", callback_data=AdminCb(action="home"))
    b.adjust(1)
    return b.as_markup()


def timers_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for key, name in TIMER_NAMES.items():
        b.button(text="✏️ " + _short(name, 38), callback_data=AdminCb(action="set_timer", value=key))
    b.button(text="⬅️ Назад", callback_data=AdminCb(action="home"))
    b.adjust(1)
    return b.as_markup()


def start_msg_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✏️ Изменить", callback_data=AdminCb(action="start_edit"))
    b.button(text="⬅️ Назад", callback_data=AdminCb(action="home"))
    b.adjust(1)
    return b.as_markup()


def channel_kb(enabled: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(
        text="🔴 Выключить проверку" if enabled else "🟢 Включить проверку",
        callback_data=AdminCb(action="ch_toggle"),
    )
    b.button(text="📢 Указать канал", callback_data=AdminCb(action="ch_set"))
    b.button(text="🔤 Текст кнопки", callback_data=AdminCb(action="ch_button"))
    b.button(text="⬅️ Назад", callback_data=AdminCb(action="home"))
    b.adjust(1)
    return b.as_markup()


def broadcast_confirm_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🚀 Отправить", callback_data=AdminCb(action="bc_go"))
    b.button(text="🚫 Отмена", callback_data=AdminCb(action="bc_cancel"))
    b.adjust(2)
    return b.as_markup()


def subscribe_kb(url: str, text: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if url:
        b.button(text=text, url=url)
    b.button(text="✅ Я подписался", callback_data=CHECK_SUB)
    b.adjust(1)
    return b.as_markup()
