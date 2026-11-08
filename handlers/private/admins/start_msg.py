from . import *

# Standard
from json import loads, dumps
from handlers.utils import CustomJSONEncoder

# __router__ !DO NOT DELETE!
start_msg_router = Router()


# __states__ !DO NOT DELETE!
class StartMsgStates(StatesGroup):
    ask_message = State()


# __buttons__ !DO NOT DELETE!


# __chat__ !DO NOT DELETE!
@start_msg_router.message(
    filters.Private(), filters.IsAdmin(),
    ((F.text == '/start_msg') | (F.text == 'Стартовое сообщение 💬'))
)
async def handle_start_msg_command(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command /start_msg from user {message.chat.id}')

    await message.answer(text=strs.admin_start_current)

    from .general import get_menu_reply_keyboard
    start_info = await db.preferences.get_by_key('start_message')
    value = start_info.get('value')
    if value == strs.general_start:
        await message.answer(text=value, reply_markup=await get_menu_reply_keyboard())
    else:
        await Message(**value).send_copy(
            chat_id=message.chat.id, reply_markup=await get_menu_reply_keyboard()
        ).as_(message.bot)

    from . import get_decline_reply_keyboard
    await message.answer(text=strs.admin_start_ask_msg, reply_markup=await get_decline_reply_keyboard())
    await state.set_state(StartMsgStates.ask_message.state)


@start_msg_router.message(StartMsgStates.ask_message)
async def handle_ask_message_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states StartMsgStates.ask_message from user {message.chat.id}')

    msg_info = loads(dumps(message.model_dump(), cls=CustomJSONEncoder))
    await db.preferences.update(
        key='start_message',
        new_data={
            'value': msg_info
        }
    )

    from .general import get_menu_reply_keyboard
    await message.answer(text=strs.admin_start_updated, reply_markup=await get_menu_reply_keyboard())
    await state.clear()
