"""Админ: рассылка с предпросмотром и подтверждением."""
from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.db import Database
from bot.keyboards.callbacks import AdminCb
from bot.keyboards.inline import back_kb, broadcast_confirm_kb
from bot.services.broadcast import is_running, start_broadcast
from bot.utils import edit_or_answer

router = Router(name="admin_broadcast")


class BroadcastStates(StatesGroup):
    message = State()
    confirm = State()


@router.callback_query(AdminCb.filter(F.action == "broadcast"))
async def broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    if is_running():
        await callback.answer(texts.BROADCAST_BUSY, show_alert=True)
        return
    await state.set_state(BroadcastStates.message)
    await edit_or_answer(callback, texts.ASK_BROADCAST, back_kb("home"))
    await callback.answer()


@router.message(BroadcastStates.message)
async def broadcast_message(message: Message, state: FSMContext, db: Database) -> None:
    count = len(await db.users.broadcast_ids())
    await state.update_data(chat_id=message.chat.id, message_id=message.message_id)
    await state.set_state(BroadcastStates.confirm)
    await message.copy_to(message.chat.id)  # предпросмотр
    await message.answer(texts.BROADCAST_CONFIRM.format(count=count), reply_markup=broadcast_confirm_kb())


@router.callback_query(BroadcastStates.confirm, AdminCb.filter(F.action == "bc_go"))
async def broadcast_go(callback: CallbackQuery, state: FSMContext, bot: Bot, db: Database) -> None:
    data = await state.get_data()
    await state.clear()
    if not start_broadcast(bot, db, data["chat_id"], data["message_id"], callback.from_user.id):
        await callback.answer(texts.BROADCAST_BUSY, show_alert=True)
        return
    await edit_or_answer(callback, texts.BROADCAST_STARTED)
    await callback.answer()


@router.callback_query(AdminCb.filter(F.action == "bc_cancel"))
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await edit_or_answer(callback, texts.BROADCAST_CANCELLED)
    await callback.answer()


@router.callback_query(AdminCb.filter(F.action == "bc_go"))
async def broadcast_expired(callback: CallbackQuery) -> None:
    # Кнопка «Отправить» нажата после перезапуска бота или повторно
    await callback.answer(texts.BROADCAST_EXPIRED, show_alert=True)
