"""Частые вопросы (коллекция faq)."""
from __future__ import annotations

from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.asynchronous.collection import AsyncCollection

from bot.utils import utcnow


def _oid(value: str) -> ObjectId | None:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


class FaqRepository:
    def __init__(self, collection: AsyncCollection) -> None:
        self.col = collection

    async def list_all(self) -> list[dict[str, Any]]:
        return await self.col.find().sort("created_at", 1).to_list(None)

    async def get(self, faq_id: str) -> dict[str, Any] | None:
        oid = _oid(faq_id)
        return await self.col.find_one({"_id": oid}) if oid else None

    async def add(self, question: str, answer: str) -> str:
        result = await self.col.insert_one(
            {"question": question, "answer": answer, "created_at": utcnow()}
        )
        return str(result.inserted_id)

    async def delete(self, faq_id: str) -> bool:
        oid = _oid(faq_id)
        if oid is None:
            return False
        result = await self.col.delete_one({"_id": oid})
        return result.deleted_count == 1
