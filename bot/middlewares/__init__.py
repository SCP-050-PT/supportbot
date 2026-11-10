from __future__ import annotations

from aiogram import Dispatcher

from bot.db import Database
from bot.middlewares.restrictions import BanMiddleware
from bot.middlewares.subscription import SubscriptionMiddleware
from bot.middlewares.user import UserMiddleware


def setup_middlewares(dp: Dispatcher, db: Database, admin_ids: frozenset[int]) -> None:
    # Порядок важен: сначала загружаем пользователя, потом бан, потом подписка
    user_mw = UserMiddleware(db, admin_ids)
    ban_mw = BanMiddleware()
    sub_mw = SubscriptionMiddleware(db)
    for observer in (dp.message, dp.callback_query):
        observer.outer_middleware(user_mw)
        observer.outer_middleware(ban_mw)
        observer.outer_middleware(sub_mw)
