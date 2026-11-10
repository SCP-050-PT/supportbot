"""Частые вопросы — просмотр (для всех)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.db import Database
from bot.keyboards.callbacks import FaqCb
from bot.keyboards.inline import faq_back_kb, faq_list_kb
from bot.keyboards.reply import Btn
from bot.utils import edit_or_answer

router = Router(name="faq")


@router.message(F.text == Btn.FAQ)
async def faq_list(message: Message, db: Database) -> None:
    items = await db.faq.list_all()
    if not items:
        await message.answer(texts.FAQ_EMPTY)
        return
    await message.answer(texts.FAQ_HEADER, reply_markup=faq_list_kb(items))


@router.callback_query(FaqCb.filter(F.action == "list"))
async def faq_list_cb(callback: CallbackQuery, db: Database) -> None:
    items = await db.faq.list_all()
    if items:
        await edit_or_answer(callback, texts.FAQ_HEADER, faq_list_kb(items))
    else:
        await edit_or_answer(callback, texts.FAQ_EMPTY)
    await callback.answer()


@router.callback_query(FaqCb.filter(F.action == "show"))
async def faq_show(callback: CallbackQuery, callback_data: FaqCb, db: Database) -> None:
    item = await db.faq.get(callback_data.faq_id)
    if item is None:
        await callback.answer(texts.FAQ_NOT_FOUND, show_alert=True)
        return
    # Ответ сохранён админом как HTML (message.html_text), вопрос экранируем
    text = f"❓ <b>{texts.esc(item['question'])}</b>\n\n{item['answer']}"
    await edit_or_answer(callback, text, faq_back_kb())
    await callback.answer()
