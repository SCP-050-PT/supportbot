"""Фоновые задачи планировщика."""
from __future__ import annotations

import logging
from datetime import timedelta

from bot.db import Database
from bot.db.constants import CloseReason
from bot.services.tickets import TicketService
from bot.utils import utcnow

logger = logging.getLogger(__name__)


async def release_stale(db: Database, ts: TicketService) -> None:
    """Возвращает в очередь обращения, где пользователь долго ждёт ответа менеджера."""
    hours = int(await db.settings.get("release_hours") or 0)
    if hours <= 0:
        return
    before = utcnow() - timedelta(hours=hours)
    for ticket in await db.tickets.find_waiting_for_staff(before):
        if ticket.get("manager_id"):
            await ts.release(ticket["_id"], ticket["manager_id"], auto=True, stale_before=before)
            logger.info("Обращение №%s автоматически возвращено в очередь", ticket["_id"])


async def close_inactive(db: Database, ts: TicketService) -> None:
    hours = int(await db.settings.get("close_hours") or 0)
    if hours <= 0:
        return
    before = utcnow() - timedelta(hours=hours)
    for ticket in await db.tickets.find_inactive(before):
        if await ts.close(ticket["_id"], CloseReason.AUTO, stale_before=before):
            logger.info("Обращение №%s закрыто автоматически", ticket["_id"])


async def cleanup_old(db: Database) -> tuple[int, int]:
    days = int(await db.settings.get("retention_days") or 0)
    if days <= 0:
        return 0, 0
    ids = await db.tickets.delete_closed_before(utcnow() - timedelta(days=days))
    deleted_messages = await db.messages.delete_for_tickets(ids)
    if ids:
        logger.info("Очистка: удалено обращений %s, сообщений %s", len(ids), deleted_messages)
    return len(ids), deleted_messages
