# Third-party
from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, ErrorEvent, CallbackQuery, ReplyKeyboardRemove, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton

# Project
import handlers.filters as filters
import handlers.middleware as middle
import config as cf
import resources.strings as strs
from database import db
from logger import bot_logger

# Routers
from .general import general_router
from .tickets import ticket_router
from .channel import channel_router

user_router = Router()
sub_routers = [
    general_router, ticket_router, channel_router
]

for router in sub_routers:
    router.message.middleware(middle.ChannelSubscriptionCheckMiddleware())
    router.message.middleware(middle.InsertUserIfNotExistMiddleware())

user_router.include_routers(*sub_routers)


async def get_decline_reply_keyboard() -> ReplyKeyboardMarkup:
    button_list = [
        [KeyboardButton(text=strs.decline_btn)],
    ]

    return ReplyKeyboardMarkup(keyboard=button_list, resize_keyboard=True, one_time_keyboard=True)


@user_router.message(F.text == strs.decline_btn)
async def handle_decline_message(message: Message, state: FSMContext):
    bot_logger.info(f'Handling decline state from user {message.from_user.id}')
    await state.clear()
    await message.answer(
        text=strs.decline_msg,
        reply_markup=ReplyKeyboardRemove()
    )
