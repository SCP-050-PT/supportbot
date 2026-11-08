# Third-party
from aiogram.dispatcher.event.bases import CancelHandler
from aiogram.exceptions import TelegramBadRequest
from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

# Project
from bot import bot
import config as cf
from logger import bot_logger
from resources import strings as strs
from database import db
from .private.users.channel import get_channel_info_menu_inline_keyboard


class ChannelSubscriptionCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_info = data.get("event_from_user")
        user_id = user_info.id
        is_admin = user_id == cf.admin_id

        # Если админ — пропускаем проверку
        if is_admin:
            return await handler(event, data)

        channel_info = await db.preferences.get_by_key("channel_info")
        if not channel_info:
            return await handler(event, data)

        is_on = channel_info.get("is_on", False)
        channel_id = channel_info.get("id", 0)

        # Если проверка канала выключена или ID невалидный — пропускаем
        if not is_on or not channel_id or channel_id == 0:
            return await handler(event, data)

        try:
            member_status = await bot.get_chat_member(
                chat_id=channel_id, user_id=user_id
            )
            if member_status.status.value in ["creator", "administrator", "member"]:
                return await handler(event, data)
            else:
                await bot.send_message(
                    chat_id=user_id,
                    text=strs.middle_check_channel,
                    reply_markup=await get_channel_info_menu_inline_keyboard(
                        user_id=user_id
                    ),
                )
                return CancelHandler()
        except TelegramBadRequest as e:
            bot_logger.error(e)
            # Если канал не найден / ошибка — просто пропускаем проверку, чтобы бот не падал
            return await handler(event, data)
        except Exception as e:
            bot_logger.error(e)
            await bot.send_message(
                chat_id=user_id, text=f"<b>Произошла внутреняя ошибка</b>\n\n{e}"
            )
            return CancelHandler()


class InsertUserIfNotExistMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        user_info = data.get('event_from_user')
        user_id = user_info.id
        full_name = user_info.full_name
        user_name = user_info.username
        user = await db.users.get_by_id(user_id=user_id)
        if not user:
            status = 'user'
            if user_id == cf.admin_id:
                status = 'admin'
            await db.users.insert(user_data={
                'user_id': user_id,
                'user_name': full_name,
                'url_name': user_name,
                'status': status
            })

        return await handler(event, data)
