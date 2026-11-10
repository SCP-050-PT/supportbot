"""Переписка по обращениям (коллекция messages)."""
from __future__ import annotations

from typing import Any

from pymongo.asynchronous.collection import AsyncCollection

from bot.utils import utcnow


class MessageRepository:
    def __init__(self, collection: AsyncCollection) -> None:
        self.col = collection

    async def add(
        self,
        ticket_id: int,
        sender: str,
        sender_id: int,
        content_type: str,
        text: str | None,
        file_id: str | None,
    ) -> None:
        # Храним file_id, а не ссылку на файл: ссылка содержит токен бота и протухает
        await self.col.insert_one({
            "ticket_id": ticket_id,
            "sender": sender,
            "sender_id": sender_id,
            "content_type": content_type,
            "text": text,
            "file_id": file_id,
            "created_at": utcnow(),
        })

    async def list_for_ticket(self, ticket_id: int, limit: int = 30) -> list[dict[str, Any]]:
        cursor = self.col.find({"ticket_id": ticket_id}).sort("created_at", -1).limit(limit)
        docs = await cursor.to_list(None)
        docs.reverse()
        return docs

    async def delete_for_tickets(self, ticket_ids: list[int]) -> int:
        if not ticket_ids:
            return 0
        result = await self.col.delete_many({"ticket_id": {"$in": ticket_ids}})
        return result.deleted_count
