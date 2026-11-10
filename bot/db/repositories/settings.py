"""Настройки, которые админ меняет прямо в боте (коллекция settings)."""
from __future__ import annotations

import copy
from typing import Any

from pymongo.asynchronous.collection import AsyncCollection

DEFAULTS: dict[str, Any] = {
    "start_message": (
        "👋 Здравствуйте! Это бот поддержки.\n\n"
        "Нажмите «📝 Создать обращение», опишите проблему — "
        "и менеджер ответит вам прямо здесь."
    ),
    "release_hours": 1,      # вернуть обращение в очередь, если менеджер молчит N часов
    "close_hours": 36,       # закрыть обращение без активности через N часов
    "retention_days": 90,    # хранить закрытые обращения N дней
    "channel": {
        "enabled": False,
        "chat_id": 0,
        "title": "",
        "url": "",
        "button_text": "📢 Подписаться",
    },
}


class SettingsRepository:
    def __init__(self, collection: AsyncCollection) -> None:
        self.col = collection

    async def get(self, key: str) -> Any:
        default = copy.deepcopy(DEFAULTS[key])
        doc = await self.col.find_one({"_id": key})
        if doc is None:
            return default
        value = doc.get("value")
        if isinstance(default, dict) and isinstance(value, dict):
            return {**default, **value}
        return value

    async def set(self, key: str, value: Any) -> None:
        await self.col.update_one({"_id": key}, {"$set": {"value": value}}, upsert=True)

    async def update_channel(self, **changes: Any) -> dict[str, Any]:
        channel = await self.get("channel")
        channel.update(changes)
        await self.set("channel", channel)
        return channel
