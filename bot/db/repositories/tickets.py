"""Обращения (коллекция tickets) и счётчик номеров (counters)."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pymongo import ReturnDocument
from pymongo.asynchronous.collection import AsyncCollection

from bot.db.constants import ACTIVE_STATUSES, Sender, TicketStatus
from bot.utils import utcnow

TicketDoc = dict[str, Any]


class TicketRepository:
    def __init__(self, collection: AsyncCollection, counters: AsyncCollection) -> None:
        self.col = collection
        self.counters = counters

    async def _next_id(self) -> int:
        doc = await self.counters.find_one_and_update(
            {"_id": "tickets"},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return int(doc["seq"])

    async def create(self, user_id: int, user_name: str, title: str, description: str) -> TicketDoc:
        now = utcnow()
        ticket: TicketDoc = {
            "_id": await self._next_id(),
            "user_id": user_id,
            "user_name": user_name,
            "title": title,
            "description": description,
            "status": TicketStatus.OPEN,
            "manager_id": None,
            "last_sender": Sender.USER,
            # С какого момента пользователь ждёт ответа менеджера (None — не ждёт)
            "waiting_since": None,
            "created_at": now,
            "updated_at": now,
            "closed_at": None,
            "closed_by": None,
        }
        await self.col.insert_one(ticket)
        return ticket

    async def get(self, ticket_id: int) -> TicketDoc | None:
        return await self.col.find_one({"_id": ticket_id})

    async def get_active_by_user(self, user_id: int) -> TicketDoc | None:
        return await self.col.find_one(
            {"user_id": user_id, "status": {"$in": list(ACTIVE_STATUSES)}}
        )

    async def list_by_user(self, user_id: int, limit: int = 10) -> list[TicketDoc]:
        cursor = self.col.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(None)

    async def list_open(self, limit: int = 20) -> list[TicketDoc]:
        cursor = self.col.find({"status": TicketStatus.OPEN}).sort("created_at", 1).limit(limit)
        return await cursor.to_list(None)

    async def assign(self, ticket_id: int, manager_id: int) -> TicketDoc | None:
        """Атомарно: принять можно только свободное открытое обращение (защита от гонки)."""
        now = utcnow()
        return await self.col.find_one_and_update(
            {"_id": ticket_id, "status": TicketStatus.OPEN, "manager_id": None},
            {"$set": {
                "status": TicketStatus.IN_PROGRESS,
                "manager_id": manager_id,
                "waiting_since": now,
                "updated_at": now,
            }},
            return_document=ReturnDocument.AFTER,
        )

    async def release(
        self, ticket_id: int, manager_id: int, stale_before: datetime | None = None
    ) -> TicketDoc | None:
        query: dict[str, Any] = {
            "_id": ticket_id,
            "status": TicketStatus.IN_PROGRESS,
            "manager_id": manager_id,
        }
        if stale_before is not None:
            query["waiting_since"] = {"$lt": stale_before}
        return await self.col.find_one_and_update(
            query,
            {"$set": {
                "status": TicketStatus.OPEN,
                "manager_id": None,
                "waiting_since": None,
                "updated_at": utcnow(),
            }},
            return_document=ReturnDocument.AFTER,
        )

    async def close(
        self, ticket_id: int, closed_by: str, stale_before: datetime | None = None
    ) -> TicketDoc | None:
        query: dict[str, Any] = {"_id": ticket_id, "status": {"$in": list(ACTIVE_STATUSES)}}
        if stale_before is not None:
            query["updated_at"] = {"$lt": stale_before}
        now = utcnow()
        return await self.col.find_one_and_update(
            query,
            {"$set": {
                "status": TicketStatus.CLOSED,
                "waiting_since": None,
                "closed_at": now,
                "closed_by": closed_by,
                "updated_at": now,
            }},
            return_document=ReturnDocument.AFTER,
        )

    async def touch(self, ticket_id: int, sender: str) -> None:
        now = utcnow()
        changes: dict[str, Any] = {"updated_at": now, "last_sender": sender}
        if sender == Sender.STAFF:
            changes["waiting_since"] = None
        await self.col.update_one({"_id": ticket_id}, {"$set": changes})
        if sender == Sender.USER:
            # Засекаем ожидание только по первому неотвеченному сообщению
            await self.col.update_one(
                {"_id": ticket_id, "status": TicketStatus.IN_PROGRESS, "waiting_since": None},
                {"$set": {"waiting_since": now}},
            )

    async def find_waiting_for_staff(self, before: datetime) -> list[TicketDoc]:
        """В работе, и пользователь ждёт ответа дольше допустимого."""
        return await self.col.find({
            "status": TicketStatus.IN_PROGRESS,
            "waiting_since": {"$lt": before},
        }).to_list(None)

    async def find_inactive(self, before: datetime) -> list[TicketDoc]:
        return await self.col.find({
            "status": {"$in": list(ACTIVE_STATUSES)},
            "updated_at": {"$lt": before},
        }).to_list(None)

    async def delete_closed_before(self, before: datetime) -> list[int]:
        cursor = self.col.find(
            {"status": TicketStatus.CLOSED, "closed_at": {"$lt": before}}, {"_id": 1}
        )
        ids = [doc["_id"] async for doc in cursor]
        if ids:
            await self.col.delete_many({"_id": {"$in": ids}})
        return ids

    async def count_by_status(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for status in (TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.CLOSED):
            result[status] = await self.col.count_documents({"status": status})
        return result
