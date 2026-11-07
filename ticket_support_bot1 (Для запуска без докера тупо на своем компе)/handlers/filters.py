# Third-party
from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.enums.chat_type import ChatType

# Project
from database import db
import resources.strings as strs
import config as cf


class IsUser(BaseFilter):  # Checks chat is private or not
    async def __call__(self, message: Message) -> bool:
        user = await db.users.get_by_id(user_id=message.from_user.id)

        if not user:
            return True

        status = user.get('status')
        if status and status == 'user':
            return True
        else:
            return False


class IsManagerOrAdmin(BaseFilter):  # Checks chat is private or not
    async def __call__(self, message: Message) -> bool:
        user = await db.users.get_by_id(user_id=message.from_user.id)
        if user:
            status = user.get('status')
            if status and status == 'manager' or message.from_user.id == cf.admin_id:
                return True
        return False


class IsManager(BaseFilter):  # Checks chat is private or not
    async def __call__(self, message: Message) -> bool:
        user = await db.users.get_by_id(user_id=message.from_user.id)
        if user:
            status = user.get('status')
            if status and status == 'manager':
                return True
        return False


class IsAdmin(BaseFilter):  # Checks chat is private or not
    async def __call__(self, message: Message) -> bool:
        return message.chat.id == cf.admin_id


class InTicket(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user = await db.users.get_by_id(user_id=message.from_user.id)
        is_in_ticket = user.get('current_ticket_id')
        if is_in_ticket:
            return True
        return False


class IsRestricted(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user = await db.users.get_by_id(user_id=message.from_user.id)
        is_muted = user.get('mute_time')
        is_banned = user.get('is_banned')

        if is_banned:
            await message.answer(text=strs.restriction_banned_forever)
            return False

        if is_muted:
            await message.answer(text=strs.restriction_before(is_muted.split('.')[0]))
            return False

        return True


class NotInState(BaseFilter):
    async def __call__(self, message: Message, state: FSMContext) -> bool:
        state = await state.get_state()
        return state is None


class Private(BaseFilter):  # Checks chat is private or not
    def __init__(self):
        self.chat_type = ChatType.PRIVATE.value

    async def __call__(self, message: Message) -> bool:
        if isinstance(self.chat_type, str):
            return message.chat.type == self.chat_type
