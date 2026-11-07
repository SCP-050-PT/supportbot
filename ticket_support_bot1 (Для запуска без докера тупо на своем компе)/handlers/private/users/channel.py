from . import *

# Project (This file doesn't see . project imports. I don't know why)
from database import db
from logger import bot_logger
from resources import strings as strs

# __router__ !DO NOT DELETE!
channel_router = Router()


# __states__ !DO NOT DELETE!


# __buttons__ !DO NOT DELETE!
async def get_channel_info_menu_inline_keyboard(user_id: int) -> InlineKeyboardMarkup:
    channel_info = await db.preferences.get_by_key('channel_info')
    channel_url = channel_info.get('url')
    button_name = channel_info.get('button_name')

    button_list = [
        [InlineKeyboardButton(text=button_name, url=channel_url)],
        [InlineKeyboardButton(text='Проверить подписку 🔔', callback_data=f'channel_subscribed_btn {user_id}')],
    ]

    @channel_router.callback_query(F.data.startswith('channel_subscribed_btn'))
    async def handle_channel_subscribed_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(
            f'Handling channel_info_menu channel_subscribed button callback from user {callback.message.chat.id}')
        data = callback.data.split()
        user_id = int(data[1])

        channel_info = await db.preferences.get_by_key('channel_info')
        id_ = channel_info.get('id')
        member_status = await callback.bot.get_chat_member(chat_id=id_, user_id=user_id)
        if member_status.status.value in ['creator', 'administrator', 'member']:
            await callback.message.delete()
            await callback.message.answer(text=strs.channel_subscribed)
        else:
            await callback.message.answer(text=strs.channel_unsubscribed)

        await callback.answer()

    return InlineKeyboardMarkup(inline_keyboard=button_list)

# __chat__ !DO NOT DELETE!
