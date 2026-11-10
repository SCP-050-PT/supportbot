"""Сборка всех роутеров. Порядок важен: сверху — более специфичные."""
from aiogram import Router

from bot.handlers import admin, common, errors, faq, staff, user


def setup_routers() -> Router:
    root = Router(name="root")
    root.include_routers(
        errors.router,
        common.router,   # /start, /id, /cancel, проверка подписки
        faq.router,      # FAQ доступен всем
        admin.router,    # только ADMIN
        staff.router,    # MANAGER и ADMIN
        user.router,     # только USER
    )
    return root
