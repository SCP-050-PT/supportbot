"""Пользователь: создание обращения, закрытие, переписка."""
from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from bot import texts
from bot.config import Config
from bot.db import Database
from bot.db.constants import CloseReason
from bot.keyboards.reply import Btn, cancel_kb, user_menu
from bot.services.tickets import TicketService
from bot.utils import fmt_dt, is_muted

router = Router(name="user_tickets")

MENU_TEXTS = {Btn.NEW_TICKET, Btn.MY_TICKETS, Btn.FAQ, Btn.CLOSE_TICKET, Btn.CANCEL}


class NewTicket(StatesGroup):
    title = State()
    description = State()


@router.message(StateFilter(None), F.text == Btn.NEW_TICKET)
async def new_ticket(
    message: Message, state: FSMContext, db_user: dict[str, Any], db: Database, config: Config
) -> None:
    if is_muted(db_user):
        await message.answer(texts.MUTED.format(until=fmt_dt(db_user["muted_until"], config.timezone)))
        return
    active = await db.tickets.get_active_by_user(db_user["_id"])
    if active:
        await message.answer(texts.ALREADY_HAS_TICKET.format(id=active["_id"]), reply_markup=user_menu(True))
        return
    await state.set_state(NewTicket.title)
    await message.answer(texts.ASK_TITLE, reply_markup=cancel_kb())


@router.message(NewTicket.title)
async def ticket_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title or len(title) > 100 or title.startswith("/") or title in MENU_TEXTS:
        await message.answer(texts.TITLE_INVALID)
        return
    await state.update_data(title=title)
    await state.set_state(NewTicket.description)
    await message.answer(texts.ASK_DESCRIPTION)


@router.message(NewTicket.description)
async def ticket_description(
    message: Message,
    state: FSMContext,
    db_user: dict[str, Any],
    db: Database,
    ticket_service: TicketService,
) -> None:
    description = (message.text or "").strip()
    if not description or len(description) > 2000 or description in MENU_TEXTS:
        await message.answer(texts.DESCRIPTION_INVALID)
        return
    data = await state.get_data()
    await state.clear()

    active = await db.tickets.get_active_by_user(db_user["_id"])
    if active:
        await message.answer(texts.ALREADY_HAS_TICKET.format(id=active["_id"]), reply_markup=user_menu(True))
        return
    ticket = await ticket_service.create(db_user, data["title"], description)
    await message.answer(texts.TICKET_CREATED.format(id=ticket["_id"]), reply_markup=user_menu(True))


@router.message(StateFilter(None), F.text == Btn.CLOSE_TICKET)
async def close_ticket(
    message: Message, db_user: dict[str, Any], db: Database, ticket_service: TicketService
) -> None:
    active = await db.tickets.get_active_by_user(db_user["_id"])
    if not active:
        await message.answer(texts.NO_ACTIVE_TICKET, reply_markup=user_menu(False))
        return
    await ticket_service.close(active["_id"], CloseReason.USER, actor_id=db_user["_id"])
    await message.answer(texts.TICKET_CLOSED_BY_USER.format(id=active["_id"]), reply_markup=user_menu(False))


@router.message(StateFilter(None), F.text == Btn.MY_TICKETS)
async def my_tickets(message: Message, db_user: dict[str, Any], db: Database, config: Config) -> None:
    tickets = await db.tickets.list_by_user(db_user["_id"])
    if not tickets:
        await message.answer(texts.NO_TICKETS)
        return
    await message.answer(
        texts.tickets_list(tickets, config.timezone, "📂 <b>Ваши обращения</b> (последние 10)")
    )


@router.message(StateFilter(None))
async def relay_to_staff(
    message: Message,
    db_user: dict[str, Any],
    db: Database,
    config: Config,
    ticket_service: TicketService,
) -> None:
    """Любое другое сообщение — это переписка по активному обращению."""
    active = await db.tickets.get_active_by_user(db_user["_id"])
    if message.text and message.text.startswith("/"):
        await message.answer(texts.USE_MENU, reply_markup=user_menu(active is not None))
        return
    if not active:
        await message.answer(texts.NO_ACTIVE_TICKET, reply_markup=user_menu(False))
        return
    if is_muted(db_user):
        await message.answer(texts.MUTED.format(until=fmt_dt(db_user["muted_until"], config.timezone)))
        return
    await ticket_service.relay_from_user(message, active)
