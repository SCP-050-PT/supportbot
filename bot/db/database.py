"""Подключение к MongoDB и создание индексов."""
from __future__ import annotations

import logging

from pymongo import ASCENDING, DESCENDING, AsyncMongoClient

from bot.db.repositories import (
    FaqRepository,
    MessageRepository,
    SettingsRepository,
    TicketRepository,
    UserRepository,
)

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, uri: str, name: str) -> None:
        # tz_aware=True — даты из базы приходят с часовым поясом (UTC)
        self.client: AsyncMongoClient = AsyncMongoClient(
            uri, tz_aware=True, serverSelectionTimeoutMS=5000
        )
        self._db = self.client[name]
        self.users = UserRepository(self._db["users"])
        self.tickets = TicketRepository(self._db["tickets"], self._db["counters"])
        self.messages = MessageRepository(self._db["messages"])
        self.faq = FaqRepository(self._db["faq"])
        self.settings = SettingsRepository(self._db["settings"])

    async def connect(self) -> None:
        await self.client.admin.command("ping")
        await self._ensure_indexes()
        logger.info("MongoDB подключена, база: %s", self._db.name)

    async def _ensure_indexes(self) -> None:
        await self._db["users"].create_index("role")
        await self._db["users"].create_index("username_lower")
        await self._db["tickets"].create_index([("status", ASCENDING), ("updated_at", ASCENDING)])
        await self._db["tickets"].create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
        await self._db["tickets"].create_index([("status", ASCENDING), ("waiting_since", ASCENDING)])
        await self._db["tickets"].create_index("manager_id")
        await self._db["tickets"].create_index("closed_at")
        await self._db["messages"].create_index([("ticket_id", ASCENDING), ("created_at", ASCENDING)])

    async def close(self) -> None:
        await self.client.close()
