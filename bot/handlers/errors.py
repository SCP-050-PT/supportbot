"""Глобальный обработчик ошибок."""
from __future__ import annotations

import logging
from contextlib import suppress

from aiogram import Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import ErrorEvent

from bot import texts

logger = logging.getLogger(__name__)
router = Router(name="errors")


@router.errors()
async def on_error(event: ErrorEvent) -> bool:
    logger.error("Ошибка при обработке апдейта %s", event.update.update_id, exc_info=event.exception)
    update = event.update
    with suppress(TelegramAPIError):
        if update.message:
            await update.message.answer(texts.UNKNOWN_ERROR)
        elif update.callback_query:
            await update.callback_query.answer(texts.UNKNOWN_ERROR, show_alert=True)
    return True
