"""Админ-панель: статистика, менеджеры, таймеры, приветствие, канал, очистка."""
from __future__ import annotations

import re
from typing import Any

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, MessageOriginChannel

from bot import texts
from bot.db import Database
from bot.db.constants import Role
from bot.keyboards.callbacks import AdminCb
from bot.keyboards.inline import (
    admin_panel_kb,
    back_kb,
    channel_kb,
    managers_kb,
    start_msg_kb,
    timers_kb,
)
from bot.keyboards.reply import Btn
from bot.services.jobs import cleanup_old
from bot.utils import edit_or_answer

router = Router(name="admin_panel")

TIMER_LIMITS: dict[str, tuple[int, int]] = {
    "release_hours": (0, 168),
    "close_hours": (0, 720),
    "retention_days": (0, 3650),
}
_CHANNEL_LINK = re.compile(r"t\.me/([A-Za-z0-9_]{4,32})/?$", re.IGNORECASE)


class PanelStates(StatesGroup):
    timer_value = State()
    start_message = State()
    channel_id = State()
    channel_url = State()
    channel_button = State()


async def _panel_text(db: Database) -> str:
    return texts.admin_panel(await db.tickets.count_by_status(), await db.users.count())


async def _timer_values(db: Database) -> dict[str, int]:
    return {key: int(await db.settings.get(key) or 0) for key in TIMER_LIMITS}


# ───── Главное меню ─────

@router.message(Command("admin"))
@router.message(F.text == Btn.ADMIN_PANEL)
async def open_panel(message: Message, state: FSMContext, db: Database) -> None:
    await state.clear()
    await message.answer(await _panel_text(db), reply_markup=admin_panel_kb())


@router.callback_query(AdminCb.filter(F.action == "home"))
async def panel_home(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    await state.clear()
    await edit_or_answer(callback, await _panel_text(db), admin_panel_kb())
    await callback.answer()


@router.callback_query(AdminCb.filter(F.action == "managers"))
async def panel_managers(callback: CallbackQuery, db: Database) -> None:
    managers = await db.users.list_by_role(Role.MANAGER)
    await edit_or_answer(callback, texts.managers_list(managers), managers_kb(managers))
    await callback.answer()


@router.callback_query(AdminCb.filter(F.action == "cleanup"))
async def panel_cleanup(callback: CallbackQuery, db: Database) -> None:
    tickets, messages = await cleanup_old(db)
    await callback.answer(texts.cleanup_done(tickets, messages), show_alert=True)


# ───── Таймеры ─────

@router.callback_query(AdminCb.filter(F.action == "timers"))
async def panel_timers(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    await state.clear()
    await edit_or_answer(callback, texts.timers(await _timer_values(db)), timers_kb())
    await callback.answer()


@router.callback_query(AdminCb.filter(F.action == "set_timer"))
async def set_timer(callback: CallbackQuery, callback_data: AdminCb, state: FSMContext) -> None:
    key = callback_data.value
    if key not in TIMER_LIMITS:
        await callback.answer()
        return
    low, high = TIMER_LIMITS[key]
    await state.set_state(PanelStates.timer_value)
    await state.update_data(timer_key=key)
    await edit_or_answer(
        callback,
        texts.ASK_TIMER_VALUE.format(name=texts.TIMER_NAMES[key], min=low, max=high),
        back_kb("timers"),
    )
    await callback.answer()


@router.message(PanelStates.timer_value)
async def timer_value(message: Message, state: FSMContext, db: Database) -> None:
    key = (await state.get_data()).get("timer_key")
    if key not in TIMER_LIMITS:
        await state.clear()
        return
    low, high = TIMER_LIMITS[key]
    raw = (message.text or "").strip()
    if not raw.isdigit() or not low <= int(raw) <= high:
        await message.answer(texts.TIMER_INVALID.format(min=low, max=high))
        return
    await db.settings.set(key, int(raw))
    await state.clear()
    await message.answer(texts.TIMER_SAVED)
    await message.answer(texts.timers(await _timer_values(db)), reply_markup=timers_kb())


# ───── Приветствие ─────

@router.callback_query(AdminCb.filter(F.action == "start_msg"))
async def start_msg(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    await state.clear()
    current = await db.settings.get("start_message")
    await edit_or_answer(callback, texts.START_MESSAGE_CURRENT.format(text=current), start_msg_kb())
    await callback.answer()


@router.callback_query(AdminCb.filter(F.action == "start_edit"))
async def start_edit(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PanelStates.start_message)
    await edit_or_answer(callback, texts.ASK_START_MESSAGE, back_kb("start_msg"))
    await callback.answer()


@router.message(PanelStates.start_message)
async def start_message_input(message: Message, state: FSMContext, db: Database) -> None:
    if not message.text:
        await message.answer(texts.TEXT_REQUIRED)
        return
    await db.settings.set("start_message", message.html_text)
    await state.clear()
    await message.answer(texts.START_MESSAGE_SAVED)


# ───── Обязательная подписка ─────

async def _send_channel(target: Message, db: Database) -> None:
    channel = await db.settings.get("channel")
    await target.answer(texts.channel_info(channel), reply_markup=channel_kb(channel["enabled"]))


@router.callback_query(AdminCb.filter(F.action == "channel"))
async def panel_channel(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    await state.clear()
    channel = await db.settings.get("channel")
    await edit_or_answer(callback, texts.channel_info(channel), channel_kb(channel["enabled"]))
    await callback.answer()


@router.callback_query(AdminCb.filter(F.action == "ch_toggle"))
async def channel_toggle(callback: CallbackQuery, db: Database) -> None:
    channel = await db.settings.get("channel")
    if not channel["enabled"] and not channel.get("chat_id"):
        await callback.answer(texts.CHANNEL_NOT_CONFIGURED, show_alert=True)
        return
    channel = await db.settings.update_channel(enabled=not channel["enabled"])
    await edit_or_answer(callback, texts.channel_info(channel), channel_kb(channel["enabled"]))
    await callback.answer()


@router.callback_query(AdminCb.filter(F.action == "ch_set"))
async def channel_set(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PanelStates.channel_id)
    await edit_or_answer(callback, texts.ASK_CHANNEL_ID, back_kb("channel"))
    await callback.answer()


def _parse_channel_ref(message: Message) -> int | str | None:
    origin = message.forward_origin
    if isinstance(origin, MessageOriginChannel):
        return origin.chat.id
    raw = (message.text or "").strip()
    if not raw:
        return None
    if raw.lstrip("-").isdigit():
        return int(raw)
    match = _CHANNEL_LINK.search(raw)
    if match:
        return "@" + match.group(1)
    if raw.startswith("@") and len(raw) > 1:
        return raw
    return None


@router.message(PanelStates.channel_id)
async def channel_id_input(message: Message, state: FSMContext, bot: Bot, db: Database) -> None:
    chat_ref = _parse_channel_ref(message)
    if chat_ref is None:
        await message.answer(texts.CHANNEL_NOT_FOUND)
        return
    try:
        chat = await bot.get_chat(chat_ref)
        me = await bot.me()
        member = await bot.get_chat_member(chat.id, me.id)
    except TelegramAPIError:
        await message.answer(texts.CHANNEL_NOT_FOUND)
        return
    status = str(getattr(member.status, "value", member.status))
    if status not in ("administrator", "creator"):
        await message.answer(texts.CHANNEL_BOT_NOT_ADMIN)
        return

    url = ("https://t.me/" + chat.username) if chat.username else (chat.invite_link or "")
    await db.settings.update_channel(chat_id=chat.id, title=chat.title or str(chat.id), url=url)
    if not url:
        await state.set_state(PanelStates.channel_url)
        await message.answer(texts.ASK_CHANNEL_URL)
        return
    await state.clear()
    await message.answer(texts.CHANNEL_SAVED)
    await _send_channel(message, db)


@router.message(PanelStates.channel_url)
async def channel_url_input(message: Message, state: FSMContext, db: Database) -> None:
    url = (message.text or "").strip()
    if not url.startswith("https://t.me/"):
        await message.answer(texts.CHANNEL_URL_INVALID)
        return
    await db.settings.update_channel(url=url)
    await state.clear()
    await message.answer(texts.CHANNEL_SAVED)
    await _send_channel(message, db)


@router.callback_query(AdminCb.filter(F.action == "ch_button"))
async def channel_button(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PanelStates.channel_button)
    await edit_or_answer(callback, texts.ASK_CHANNEL_BUTTON, back_kb("channel"))
    await callback.answer()


@router.message(PanelStates.channel_button)
async def channel_button_input(message: Message, state: FSMContext, db: Database) -> None:
    text = (message.text or "").strip()
    if not text or len(text) > 40:
        await message.answer(texts.CHANNEL_BUTTON_INVALID)
        return
    await db.settings.update_channel(button_text=text)
    await state.clear()
    await message.answer(texts.CHANNEL_BUTTON_SAVED)
    await _send_channel(message, db)
