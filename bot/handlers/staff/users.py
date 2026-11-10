"""Менеджеры и админы: поиск пользователя, мут, бан, роли."""
from __future__ import annotations

import re
from datetime import timedelta
from typing import Any

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.config import Config
from bot.db import Database
from bot.db.constants import STAFF_ROLES, CloseReason, Role
from bot.keyboards.callbacks import UserCb
from bot.keyboards.inline import managers_kb, open_tickets_kb, user_card_kb
from bot.keyboards.reply import Btn, cancel_kb, staff_menu
from bot.services.tickets import TicketService
from bot.utils import edit_or_answer, fmt_dt, utcnow

router = Router(name="staff_users")

_TG_LINK = re.compile(r"t\.me/([A-Za-z0-9_]{4,32})", re.IGNORECASE)


class FindUser(StatesGroup):
    query = State()


async def _resolve(db: Database, query: str) -> dict[str, Any] | None:
    q = query.strip()
    if q.isdigit():
        return await db.users.get(int(q))
    match = _TG_LINK.search(q)
    if match:
        q = match.group(1)
    q = q.lstrip("@").strip()
    return await db.users.find_by_username(q) if q else None


async def _card_text(db: Database, target: dict[str, Any], config: Config) -> str:
    active = await db.tickets.get_active_by_user(target["_id"])
    return texts.user_card(target, active, config.timezone)


@router.message(StateFilter(None), F.text == Btn.FIND_USER)
async def find_user(message: Message, state: FSMContext) -> None:
    await state.set_state(FindUser.query)
    await message.answer(texts.ASK_USER_QUERY, reply_markup=cancel_kb())


@router.message(FindUser.query)
async def find_user_query(
    message: Message, state: FSMContext, db: Database, db_user: dict[str, Any], config: Config
) -> None:
    target = await _resolve(db, message.text or "")
    if target is None:
        await message.answer(texts.USER_NOT_FOUND)
        return
    await state.clear()
    is_admin = db_user.get("role") == Role.ADMIN
    await message.answer(texts.USER_FOUND, reply_markup=staff_menu(is_admin))
    await message.answer(await _card_text(db, target, config), reply_markup=user_card_kb(target, is_admin))


@router.callback_query(UserCb.filter())
async def user_action(
    callback: CallbackQuery,
    callback_data: UserCb,
    bot: Bot,
    db: Database,
    db_user: dict[str, Any],
    config: Config,
    ticket_service: TicketService,
) -> None:
    viewer_is_admin = db_user.get("role") == Role.ADMIN
    target = await db.users.get(callback_data.user_id)
    if target is None:
        await callback.answer(texts.USER_NOT_FOUND, show_alert=True)
        return
    uid = target["_id"]
    action = callback_data.action

    # ── Список обращений пользователя ──
    if action == "tickets":
        await callback.answer()
        tickets = await db.tickets.list_by_user(uid)
        if not tickets:
            await bot.send_message(callback.from_user.id, texts.NO_USER_TICKETS)
            return
        title = f"📂 <b>Обращения:</b> {texts.esc(target.get('full_name'))}"
        await bot.send_message(
            callback.from_user.id,
            texts.tickets_list(tickets, config.timezone, title),
            reply_markup=open_tickets_kb(tickets),
        )
        return

    # ── Роли (только админ) ──
    if action in ("promote", "demote"):
        if not viewer_is_admin:
            await callback.answer(texts.ADMIN_ONLY, show_alert=True)
            return
        if target.get("role") == Role.ADMIN:
            await callback.answer(texts.ADMIN_ROLE_LOCKED, show_alert=True)
            return
        if action == "promote":
            target = await db.users.set_role(uid, Role.MANAGER) or target
            await ticket_service.send(uid, texts.YOU_ARE_MANAGER)
        else:
            current = target.get("current_ticket_id")
            if current:
                await ticket_service.release(current, uid)  # вернуть его обращение в очередь
            target = await db.users.set_role(uid, Role.USER) or target
            await ticket_service.send(uid, texts.YOU_ARE_USER)
        await callback.answer(texts.ROLE_CHANGED)
        if callback_data.value == 1:  # нажали из списка менеджеров — обновляем список
            managers = await db.users.list_by_role(Role.MANAGER)
            await edit_or_answer(callback, texts.managers_list(managers), managers_kb(managers))
        else:
            await edit_or_answer(
                callback, await _card_text(db, target, config), user_card_kb(target, viewer_is_admin)
            )
        return

    # ── Ограничения (сотрудников ограничивать нельзя) ──
    if target.get("role") in STAFF_ROLES:
        await callback.answer(texts.STAFF_PROTECTED, show_alert=True)
        return

    if action == "mute":
        until = utcnow() + timedelta(hours=max(1, callback_data.value))
        target = await db.users.set_mute(uid, until) or target
        note = texts.USER_MUTED.format(until=fmt_dt(until, config.timezone))
    elif action == "unmute":
        target = await db.users.set_mute(uid, None) or target
        note = texts.USER_UNMUTED
    elif action == "ban":
        target = await db.users.set_ban(uid, True) or target
        active = await db.tickets.get_active_by_user(uid)
        if active:
            await ticket_service.close(active["_id"], CloseReason.STAFF, actor_id=db_user["_id"])
        note = texts.USER_BANNED
    elif action == "unban":
        target = await db.users.set_ban(uid, False) or target
        note = texts.USER_UNBANNED
    else:
        await callback.answer()
        return

    await callback.answer(note)
    await edit_or_answer(callback, await _card_text(db, target, config), user_card_kb(target, viewer_is_admin))
