"""Команды для всех: /start, /id, /cancel и проверка подписки."""
from __future__ import annotations

from typing import Any

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.db import Database
from bot.db.constants import STAFF_ROLES
from bot.keyboards.callbacks import CHECK_SUB
from bot.keyboards.reply import Btn, menu_for
from bot.services.subscription import is_subscribed
from bot.utils import safe_delete

router = Router(name="common")


async def _send_start(bot: Bot, chat_id: int, db_user: dict[str, Any], db: Database) -> None:
    kb = await menu_for(db_user, db)
    role = db_user.get("role")
    if role in STAFF_ROLES:
        text = texts.STAFF_HELLO.format(role=texts.ROLE_LABELS.get(role, role))
    else:
        text = await db.settings.get("start_message")
    await bot.send_message(chat_id, text, reply_markup=kb)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot, db_user: dict[str, Any], db: Database) -> None:
    await state.clear()
    await _send_start(bot, message.chat.id, db_user, db)


@router.message(Command("id"))
async def cmd_id(message: Message) -> None:
    await message.answer(texts.USER_ID.format(id=message.chat.id))


@router.message(Command("cancel"))
@router.message(F.text == Btn.CANCEL)
async def cmd_cancel(message: Message, state: FSMContext, db_user: dict[str, Any], db: Database) -> None:
    current = await state.get_state()
    await state.clear()
    await message.answer(
        texts.CANCELLED if current else texts.NOTHING_TO_CANCEL,
        reply_markup=await menu_for(db_user, db),
    )


@router.callback_query(F.data == CHECK_SUB)
async def check_subscription(callback: CallbackQuery, bot: Bot, db_user: dict[str, Any], db: Database) -> None:
    channel = await db.settings.get("channel")
    ok = (
        not channel.get("enabled")
        or not channel.get("chat_id")
        or await is_subscribed(bot, channel["chat_id"], callback.from_user.id)
    )
    if not ok:
        await callback.answer(texts.SUBSCRIBE_NOT_YET, show_alert=True)
        return
    await callback.answer(texts.SUBSCRIBE_OK)
    await safe_delete(callback.message)
    await _send_start(bot, callback.from_user.id, db_user, db)
