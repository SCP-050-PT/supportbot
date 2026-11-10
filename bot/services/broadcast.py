"""Рассылка в фоне, с паузами и учётом флуд-лимитов Telegram."""
from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError, TelegramRetryAfter

from bot import texts
from bot.db import Database

logger = logging.getLogger(__name__)

_tasks: set[asyncio.Task] = set()


def is_running() -> bool:
    return any(not task.done() for task in _tasks)


def start_broadcast(bot: Bot, db: Database, from_chat_id: int, message_id: int, report_to: int) -> bool:
    if is_running():
        return False
    task = asyncio.create_task(_run(bot, db, from_chat_id, message_id, report_to))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return True


async def _run(bot: Bot, db: Database, from_chat_id: int, message_id: int, report_to: int) -> None:
    sent = blocked = failed = 0
    try:
        user_ids = await db.users.broadcast_ids()
        logger.info("Рассылка: получателей %s", len(user_ids))
        for user_id in user_ids:
            for _ in range(3):
                try:
                    await bot.copy_message(user_id, from_chat_id, message_id)
                    sent += 1
                except TelegramRetryAfter as exc:
                    await asyncio.sleep(exc.retry_after + 1)
                    continue
                except TelegramForbiddenError:
                    blocked += 1
                except TelegramAPIError as exc:
                    failed += 1
                    logger.debug("Рассылка: %s — %s", user_id, exc)
                break
            await asyncio.sleep(0.05)  # ~20 сообщений в секунду, ниже лимита Telegram
    except Exception:
        logger.exception("Рассылка прервана")
    finally:
        logger.info("Рассылка завершена: %s/%s/%s", sent, blocked, failed)
        with suppress(TelegramAPIError):
            await bot.send_message(report_to, texts.broadcast_report(sent, blocked, failed))
