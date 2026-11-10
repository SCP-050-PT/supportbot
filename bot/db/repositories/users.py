"""Пользователи и сотрудники (коллекция users)."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pymongo import ReturnDocument
from pymongo.asynchronous.collection import AsyncCollection

from bot.db.constants import STAFF_ROLES, Role
from bot.utils import utcnow

UserDoc = dict[str, Any]


class UserRepository:
    def __init__(self, collection: AsyncCollection) -> None:
        self.col = collection

    async def upsert_from_telegram(
        self, user_id: int, full_name: str, username: str | None, default_role: str
    ) -> UserDoc:
        now = utcnow()
        return await self.col.find_one_and_update(
            {"_id": user_id},
            {
                "$set": {
                    "full_name": full_name,
                    "username": username,
                    "username_lower": username.lower() if username else None,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "role": default_role,
                    "current_ticket_id": None,
                    "muted_until": None,
                    "is_banned": False,
                    "created_at": now,
                },
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def get(self, user_id: int) -> UserDoc | None:
        return await self.col.find_one({"_id": user_id})

    async def find_by_username(self, username: str) -> UserDoc | None:
        return await self.col.find_one({"username_lower": username.lower()})

    async def _update(self, user_id: int, changes: dict[str, Any]) -> UserDoc | None:
        return await self.col.find_one_and_update(
            {"_id": user_id}, {"$set": changes}, return_document=ReturnDocument.AFTER
        )

    async def set_role(self, user_id: int, role: str) -> UserDoc | None:
        return await self._update(user_id, {"role": role})

    async def set_mute(self, user_id: int, until: datetime | None) -> UserDoc | None:
        return await self._update(user_id, {"muted_until": until})

    async def set_ban(self, user_id: int, banned: bool) -> UserDoc | None:
        return await self._update(user_id, {"is_banned": banned})

    async def list_by_role(self, role: str) -> list[UserDoc]:
        return await self.col.find({"role": role}).sort("created_at", 1).to_list(None)

    async def list_staff(self) -> list[UserDoc]:
        return await self.col.find(
            {"role": {"$in": list(STAFF_ROLES)}, "is_banned": {"$ne": True}}
        ).to_list(None)

    # ── «Слот» менеджера: одно активное обращение на человека ──

    async def take_slot(self, manager_id: int, ticket_id: int) -> bool:
        """Атомарно занимает слот, только если он свободен."""
        result = await self.col.update_one(
            {"_id": manager_id, "current_ticket_id": None},
            {"$set": {"current_ticket_id": ticket_id}},
        )
        return result.modified_count == 1

    async def free_slot(self, manager_id: int, ticket_id: int) -> None:
        await self.col.update_one(
            {"_id": manager_id, "current_ticket_id": ticket_id},
            {"$set": {"current_ticket_id": None}},
        )

    async def broadcast_ids(self) -> list[int]:
        cursor = self.col.find({"role": Role.USER, "is_banned": {"$ne": True}}, {"_id": 1})
        return [doc["_id"] async for doc in cursor]

    async def count(self) -> int:
        return await self.col.count_documents({})
