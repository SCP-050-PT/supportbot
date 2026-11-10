"""Бизнес-логика обращений: создание, принятие, пересылка, закрытие."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Awaitable, Callable
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import Message, ReplyKeyboardMarkup

from bot import texts
from bot.db import Database
from bot.db.constants import CloseReason, Sender, TicketStatus
from bot.keyboards.inline import accept_ticket_kb
from bot.keyboards.reply import user_menu
from bot.utils import content_type_of, extract_file_id

logger = logging.getLogger(__name__)


class AcceptResult:
    OK = "ok"
    BUSY = "busy"
    TAKEN = "taken"
    CLOSED = "closed"
    NOT_FOUND = "not_found"


class TicketService:
    def __init__(self, bot: Bot, db: Database, tz: ZoneInfo) -> None:
        self.bot = bot
        self.db = db
        self.tz = tz

    # ───── Безопасная отправка ─────

    async def _call(self, factory: Callable[[], Awaitable[Any]]) -> bool:
        """Выполняет запрос к Telegram с учётом флуд-лимитов. True — успешно."""
        for _ in range(3):
            try:
                await factory()
                return True
            except TelegramRetryAfter as exc:
                await asyncio.sleep(exc.retry_after + 0.5)
            except TelegramForbiddenError:
                return False  # пользователь заблокировал бота
            except TelegramAPIError as exc:
                logger.warning("Ошибка Telegram API: %s", exc)
                return False
        return False

    async def send(
        self, chat_id: int, text: str, reply_markup: Any | None = None
    ) -> bool:
        return await self._call(
            lambda: self.bot.send_message(chat_id, text, reply_markup=reply_markup)
        )

    async def notify_staff(
        self, ticket: dict[str, Any], prefix: str, exclude: int | None = None
    ) -> None:
        card = texts.ticket_card(ticket, self.tz, prefix)
        kb = accept_ticket_kb(ticket["_id"])
        for member in await self.db.users.list_staff():
            if member["_id"] == exclude:
                continue
            await self.send(member["_id"], card, reply_markup=kb)
            await asyncio.sleep(0.05)

    # ───── Жизненный цикл обращения ─────

    async def create(self, db_user: dict[str, Any], title: str, description: str) -> dict[str, Any]:
        name = db_user.get("full_name") or str(db_user["_id"])
        ticket = await self.db.tickets.create(db_user["_id"], name, title, description)
        await self.db.messages.add(ticket["_id"], Sender.USER, db_user["_id"], "text", description, None)
        await self.notify_staff(ticket, texts.STAFF_NEW_TICKET)
        return ticket

    async def heal_slot(self, manager: dict[str, Any]) -> dict[str, Any]:
        """Чинит «зависший» слот менеджера, если его обращение уже не в работе у него."""
        ticket_id = manager.get("current_ticket_id")
        if ticket_id is None:
            return manager
        ticket = await self.db.tickets.get(ticket_id)
        if (
            ticket is not None
            and ticket["status"] == TicketStatus.IN_PROGRESS
            and ticket.get("manager_id") == manager["_id"]
        ):
            return manager
        await self.db.users.free_slot(manager["_id"], ticket_id)
        return {**manager, "current_ticket_id": None}

    async def get_current(self, manager_id: int) -> dict[str, Any] | None:
        manager = await self.db.users.get(manager_id)
        if manager is None:
            return None
        manager = await self.heal_slot(manager)
        ticket_id = manager.get("current_ticket_id")
        return await self.db.tickets.get(ticket_id) if ticket_id else None

    async def accept(self, ticket_id: int, manager_id: int) -> tuple[str, dict[str, Any] | None]:
        ticket = await self.db.tickets.get(ticket_id)
        if ticket is None:
            return AcceptResult.NOT_FOUND, None
        if ticket["status"] == TicketStatus.CLOSED:
            return AcceptResult.CLOSED, ticket
        if ticket["status"] == TicketStatus.IN_PROGRESS:
            if ticket.get("manager_id") == manager_id:
                return AcceptResult.OK, ticket
            return AcceptResult.TAKEN, ticket

        manager = await self.db.users.get(manager_id)
        if manager is None:
            return AcceptResult.NOT_FOUND, None
        manager = await self.heal_slot(manager)
        if manager.get("current_ticket_id"):
            return AcceptResult.BUSY, ticket

        # 1) атомарно занимаем слот менеджера, 2) атомарно забираем обращение
        if not await self.db.users.take_slot(manager_id, ticket_id):
            return AcceptResult.BUSY, ticket
        updated = await self.db.tickets.assign(ticket_id, manager_id)
        if updated is None:
            await self.db.users.free_slot(manager_id, ticket_id)  # откат
            fresh = await self.db.tickets.get(ticket_id)
            if fresh is None:
                return AcceptResult.NOT_FOUND, None
            if fresh["status"] == TicketStatus.CLOSED:
                return AcceptResult.CLOSED, fresh
            return AcceptResult.TAKEN, fresh

        await self.send(updated["user_id"], texts.USER_TICKET_ACCEPTED.format(id=ticket_id))
        return AcceptResult.OK, updated

    async def release(
        self,
        ticket_id: int,
        manager_id: int,
        auto: bool = False,
        stale_before: datetime | None = None,
    ) -> dict[str, Any] | None:
        ticket = await self.db.tickets.release(ticket_id, manager_id, stale_before)
        if ticket is None:
            if not auto:
                await self.db.users.free_slot(manager_id, ticket_id)
            return None
        await self.db.users.free_slot(manager_id, ticket_id)
        if auto:
            await self.send(manager_id, texts.STAFF_AUTO_RELEASED.format(id=ticket_id))
        await self.send(ticket["user_id"], texts.USER_TICKET_RELEASED.format(id=ticket_id))
        await self.notify_staff(ticket, texts.STAFF_TICKET_RETURNED, exclude=manager_id)
        return ticket

    async def close(
        self,
        ticket_id: int,
        reason: str,
        actor_id: int | None = None,
        stale_before: datetime | None = None,
    ) -> dict[str, Any] | None:
        ticket = await self.db.tickets.close(ticket_id, reason, stale_before)
        if ticket is None:
            return None
        manager_id = ticket.get("manager_id")
        if manager_id:
            await self.db.users.free_slot(manager_id, ticket_id)

        reason_text = texts.CLOSE_REASONS.get(reason, "")
        if reason != CloseReason.USER:
            menu: ReplyKeyboardMarkup = user_menu(False)
            await self.send(
                ticket["user_id"],
                texts.USER_TICKET_CLOSED.format(id=ticket_id, reason=reason_text),
                reply_markup=menu,
            )
        if manager_id and manager_id != actor_id:
            await self.send(
                manager_id, texts.STAFF_TICKET_CLOSED_NOTIFY.format(id=ticket_id, reason=reason_text)
            )
        return ticket

    # ───── Переписка ─────

    async def _save(self, ticket_id: int, sender: str, message: Message) -> None:
        await self.db.messages.add(
            ticket_id,
            sender,
            message.from_user.id if message.from_user else 0,
            content_type_of(message),
            message.text or message.caption,
            extract_file_id(message),
        )

    async def relay_from_user(self, message: Message, ticket: dict[str, Any]) -> None:
        await self._save(ticket["_id"], Sender.USER, message)
        await self.db.tickets.touch(ticket["_id"], Sender.USER)
        manager_id = ticket.get("manager_id")
        if ticket["status"] == TicketStatus.IN_PROGRESS and manager_id:
            if not await self._call(lambda: message.copy_to(manager_id)):
                await message.answer(texts.NOT_DELIVERED)
        else:
            await message.answer(texts.MESSAGE_QUEUED.format(id=ticket["_id"]))

    async def relay_from_staff(self, message: Message, ticket: dict[str, Any]) -> None:
        if not await self._call(lambda: message.copy_to(ticket["user_id"])):
            await message.answer(texts.USER_UNAVAILABLE)
            return
        await self._save(ticket["_id"], Sender.STAFF, message)
        await self.db.tickets.touch(ticket["_id"], Sender.STAFF)

    async def send_history(self, chat_id: int, ticket: dict[str, Any]) -> None:
        messages = await self.db.messages.list_for_ticket(ticket["_id"])
        await self.send(chat_id, texts.ticket_history(ticket, messages, self.tz))
