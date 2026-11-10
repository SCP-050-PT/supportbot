"""Мелкие вспомогательные функции."""
from __future__ import annotations

from contextlib import suppress
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def fmt_dt(value: datetime | None, tz: ZoneInfo) -> str:
    if value is None:
        return "—"
    return _aware(value).astimezone(tz).strftime("%d.%m.%Y %H:%M")


def is_muted(db_user: dict[str, Any]) -> bool:
    until = db_user.get("muted_until")
    return until is not None and _aware(until) > utcnow()


def extract_file_id(message: Message) -> str | None:
    if message.photo:
        return message.photo[-1].file_id
    for attr in ("video", "document", "audio", "voice", "video_note", "sticker", "animation"):
        media = getattr(message, attr, None)
        if media is not None:
            return media.file_id
    return None


def content_type_of(message: Message) -> str:
    value = message.content_type
    return str(getattr(value, "value", value))


async def safe_delete(message: object) -> None:
    if isinstance(message, Message):
        with suppress(TelegramBadRequest):
            await message.delete()


async def edit_or_answer(
    callback: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    """Редактирует сообщение с кнопкой, а если нельзя — отправляет новое."""
    message = callback.message
    if isinstance(message, Message):
        try:
            await message.edit_text(text, reply_markup=reply_markup)
            return
        except TelegramBadRequest as exc:
            if "message is not modified" in str(exc):
                return
    await callback.bot.send_message(callback.from_user.id, text, reply_markup=reply_markup)
