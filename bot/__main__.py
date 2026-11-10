"""Точка входа: python -m bot"""
from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.fsm.storage.memory import MemoryStorage
from pymongo.errors import PyMongoError

from bot.config import ConfigError, load_config
from bot.db import Database
from bot.handlers import setup_routers
from bot.logger import setup_logging
from bot.middlewares import setup_middlewares
from bot.scheduler import setup_scheduler
from bot.services.tickets import TicketService

logger = logging.getLogger("bot")


async def main() -> None:
    config = load_config()
    setup_logging(config.log_level, config.logs_dir)

    db = Database(config.mongo_uri, config.mongo_db)
    try:
        await db.connect()
    except PyMongoError as exc:
        logger.critical("Не удалось подключиться к MongoDB (%s): %s", config.mongo_uri, exc)
        await db.close()
        return

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True),
    )
    ticket_service = TicketService(bot, db, config.timezone)

    # Всё, что передано в Dispatcher, доступно в хендлерах по имени аргумента
    dp = Dispatcher(storage=MemoryStorage(), db=db, config=config, ticket_service=ticket_service)
    setup_middlewares(dp, db, config.admin_ids)
    dp.include_router(setup_routers())

    scheduler = setup_scheduler(db, ticket_service, config.timezone)
    try:
        try:
            me = await bot.get_me()
        except TelegramUnauthorizedError:
            logger.critical("Telegram отклонил BOT_TOKEN — проверьте токен в .env")
            return
        await bot.delete_webhook(drop_pending_updates=False)
        scheduler.start()
        logger.info("Бот @%s запущен", me.username)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)
        await bot.session.close()
        await db.close()
        logger.info("Бот остановлен")


def run() -> None:
    try:
        asyncio.run(main())
    except ConfigError as exc:
        print(f"Ошибка в настройках .env: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()
