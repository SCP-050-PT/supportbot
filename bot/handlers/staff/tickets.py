"""Менеджеры: очередь, принятие, переписка, закрытие."""
from __future__ import annotations

from contextlib import suppress
from typing import Any

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.config import Config
from bot.db import Database
from bot.db.constants import CloseReason, Role, TicketStatus
from bot.keyboards.callbacks import TicketCb
from bot.keyboards.inline import accept_ticket_kb, open_tickets_kb
from bot.keyboards.reply import Btn, staff_menu
from bot.services.tickets import AcceptResult, TicketService

router = Router(name="staff_tickets")


@router.callback_query(TicketCb.filter(F.action == "view"))
async def view_ticket(callback: CallbackQuery, callback_data: TicketCb, bot: Bot, db: Database, config: Config) -> None:
    ticket = await db.tickets.get(callback_data.ticket_id)
    if ticket is None:
        await callback.answer(texts.ACCEPT_ERRORS["not_found"], show_alert=True)
        return
    await callback.answer()
    kb = accept_ticket_kb(ticket["_id"]) if ticket["status"] == TicketStatus.OPEN else None
    await bot.send_message(callback.from_user.id, texts.ticket_card(ticket, config.timezone), reply_markup=kb)


@router.callback_query(TicketCb.filter(F.action == "accept"))
async def accept_ticket(
    callback: CallbackQuery,
    callback_data: TicketCb,
    bot: Bot,
    db_user: dict[str, Any],
    ticket_service: TicketService,
) -> None:
    result, ticket = await ticket_service.accept(callback_data.ticket_id, db_user["_id"])
    if result != AcceptResult.OK or ticket is None:
        await callback.answer(texts.ACCEPT_ERRORS.get(result, texts.UNKNOWN_ERROR), show_alert=True)
        return
    await callback.answer()
    if isinstance(callback.message, Message):
        with suppress(TelegramBadRequest):
            await callback.message.edit_reply_markup(reply_markup=None)
    await ticket_service.send_history(callback.from_user.id, ticket)
    await bot.send_message(
        callback.from_user.id,
        texts.STAFF_ACCEPTED.format(id=ticket["_id"]),
        reply_markup=staff_menu(db_user.get("role") == Role.ADMIN),
    )


@router.callback_query(TicketCb.filter(F.action == "history"))
async def ticket_history(
    callback: CallbackQuery, callback_data: TicketCb, db: Database, ticket_service: TicketService
) -> None:
    ticket = await db.tickets.get(callback_data.ticket_id)
    if ticket is None:
        await callback.answer(texts.ACCEPT_ERRORS["not_found"], show_alert=True)
        return
    await callback.answer()
    await ticket_service.send_history(callback.from_user.id, ticket)


@router.message(StateFilter(None), F.text == Btn.OPEN_TICKETS)
async def open_tickets(message: Message, db: Database) -> None:
    tickets = await db.tickets.list_open()
    if not tickets:
        await message.answer(texts.NO_OPEN_TICKETS)
        return
    await message.answer(
        texts.OPEN_TICKETS_HEADER.format(count=len(tickets)), reply_markup=open_tickets_kb(tickets)
    )


@router.message(StateFilter(None), F.text == Btn.CURRENT_TICKET)
async def current_ticket(
    message: Message, db_user: dict[str, Any], config: Config, ticket_service: TicketService
) -> None:
    ticket = await ticket_service.get_current(db_user["_id"])
    if ticket is None:
        await message.answer(texts.STAFF_NO_CURRENT)
        return
    await message.answer(texts.ticket_card(ticket, config.timezone))
    await ticket_service.send_history(message.chat.id, ticket)


@router.message(StateFilter(None), F.text == Btn.RELEASE)
async def release_ticket(message: Message, db_user: dict[str, Any], ticket_service: TicketService) -> None:
    ticket = await ticket_service.get_current(db_user["_id"])
    if ticket is None:
        await message.answer(texts.STAFF_NO_CURRENT)
        return
    released = await ticket_service.release(ticket["_id"], db_user["_id"])
    await message.answer(
        texts.STAFF_RELEASED.format(id=ticket["_id"]) if released else texts.STAFF_NO_CURRENT
    )


@router.message(StateFilter(None), F.text == Btn.STAFF_CLOSE)
async def close_ticket(message: Message, db_user: dict[str, Any], ticket_service: TicketService) -> None:
    ticket = await ticket_service.get_current(db_user["_id"])
    if ticket is None:
        await message.answer(texts.STAFF_NO_CURRENT)
        return
    closed = await ticket_service.close(ticket["_id"], CloseReason.STAFF, actor_id=db_user["_id"])
    await message.answer(texts.STAFF_CLOSED.format(id=ticket["_id"]) if closed else texts.STAFF_NO_CURRENT)


@router.message(StateFilter(None))
async def relay_to_user(message: Message, db_user: dict[str, Any], ticket_service: TicketService) -> None:
    """Любое другое сообщение менеджера уходит пользователю текущего обращения."""
    if message.text and message.text.startswith("/"):
        await message.answer(texts.USE_MENU, reply_markup=staff_menu(db_user.get("role") == Role.ADMIN))
        return
    ticket = await ticket_service.get_current(db_user["_id"])
    if ticket is None:
        await message.answer(texts.STAFF_NO_CURRENT)
        return
    await ticket_service.relay_from_staff(message, ticket)
