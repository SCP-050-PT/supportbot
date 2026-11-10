"""Фильтр по роли пользователя из базы."""
from __future__ import annotations

from typing import Any

from aiogram.filters import Filter
from aiogram.types import TelegramObject


class RoleFilter(Filter):
    def __init__(self, *roles: str) -> None:
        self.roles = frozenset(roles)

    async def __call__(self, event: TelegramObject, db_user: dict[str, Any] | None = None) -> bool:
        return db_user is not None and db_user.get("role") in self.roles
