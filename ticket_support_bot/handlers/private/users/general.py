from . import *

# __router__ !DO NOT DELETE!
general_router = Router()


# __states__ !DO NOT DELETE!


# __buttons__ !DO NOT DELETE!
async def get_menu_reply_keyboard() -> ReplyKeyboardMarkup:
    button_list = [
        [KeyboardButton(text='Создать тикет 💬'),
         KeyboardButton(text='Мои тикеты 📂')],
        [KeyboardButton(text='FAQ ❓')],

    ]

    return ReplyKeyboardMarkup(keyboard=button_list, resize_keyboard=True)


# __chat__ !DO NOT DELETE!
@general_router.message((Command('start')), filters.Private(), filters.IsUser())
async def handle_start_command(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command /start from user {message.chat.id}')

    start_info = await db.preferences.get_by_key('start_message')
    value = start_info.get('value')
    if value == strs.general_start:
        await message.answer(text=value, reply_markup=await get_menu_reply_keyboard())
    else:
        await Message(**value).send_copy(
            chat_id=message.chat.id, reply_markup=await get_menu_reply_keyboard()
        ).as_(message.bot)


@general_router.message(Command('help'), filters.Private(), filters.IsUser())
async def handle_help_command(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command /help from user {message.chat.id}')
    await message.answer(text=strs.general_help, reply_markup=await get_menu_reply_keyboard())