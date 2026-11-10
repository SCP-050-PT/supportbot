"""Админ: управление FAQ."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.db import Database
from bot.keyboards.callbacks import AdminCb, FaqCb
from bot.keyboards.inline import back_kb, faq_admin_kb
from bot.utils import edit_or_answer

router = Router(name="admin_faq")


class FaqStates(StatesGroup):
    question = State()
    answer = State()


@router.callback_query(AdminCb.filter(F.action == "faq"))
async def faq_admin(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    await state.clear()
    items = await db.faq.list_all()
    await edit_or_answer(callback, texts.FAQ_ADMIN_HEADER if items else texts.FAQ_EMPTY, faq_admin_kb(items))
    await callback.answer()


@router.callback_query(AdminCb.filter(F.action == "faq_add"))
async def faq_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(FaqStates.question)
    await edit_or_answer(callback, texts.ASK_FAQ_QUESTION, back_kb("faq"))
    await callback.answer()


@router.message(FaqStates.question)
async def faq_question(message: Message, state: FSMContext) -> None:
    question = (message.text or "").strip()
    if not question or len(question) > 200:
        await message.answer(texts.FAQ_QUESTION_INVALID)
        return
    await state.update_data(question=question)
    await state.set_state(FaqStates.answer)
    await message.answer(texts.ASK_FAQ_ANSWER)


@router.message(FaqStates.answer)
async def faq_answer(message: Message, state: FSMContext, db: Database) -> None:
    if not message.text:
        await message.answer(texts.TEXT_REQUIRED)
        return
    data = await state.get_data()
    await state.clear()
    await db.faq.add(data["question"], message.html_text)
    await message.answer(texts.FAQ_ADDED)
    items = await db.faq.list_all()
    await message.answer(texts.FAQ_ADMIN_HEADER, reply_markup=faq_admin_kb(items))


@router.callback_query(FaqCb.filter(F.action == "del"))
async def faq_delete(callback: CallbackQuery, callback_data: FaqCb, db: Database) -> None:
    deleted = await db.faq.delete(callback_data.faq_id)
    await callback.answer(texts.FAQ_DELETED if deleted else texts.FAQ_NOT_FOUND)
    items = await db.faq.list_all()
    await edit_or_answer(callback, texts.FAQ_ADMIN_HEADER if items else texts.FAQ_EMPTY, faq_admin_kb(items))
