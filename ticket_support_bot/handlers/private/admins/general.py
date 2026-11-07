from . import *

# __router__ !DO NOT DELETE!
general_router = Router()


# __states__ !DO NOT DELETE!

# __buttons__ !DO NOT DELETE!
async def get_menu_reply_keyboard() -> ReplyKeyboardMarkup:
    button_list = [
        [KeyboardButton(text='Изменить FAQ ❓'),
         KeyboardButton(text='Изменить канал подписки 🌐')],
        [KeyboardButton(text='Найти пользователя 🔎'),
         KeyboardButton(text='Мои тикеты 📂')],
        [KeyboardButton(text='Отправить рассылку 📬'),
         KeyboardButton(text='Стартовое сообщение 💬')],
        [KeyboardButton(text='Изменить время авто осовобождения/закрытия 🕒')],
        [KeyboardButton(text='Удалить тикеты 🗑️')],
        [KeyboardButton(text='Режим менеджера 💼')]
    ]

    return ReplyKeyboardMarkup(keyboard=button_list, resize_keyboard=True)


# __chat__ !DO NOT DELETE!
@general_router.message((Command('start')), filters.Private(), filters.IsAdmin(), )
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


@general_router.message(Command('help'), filters.Private(), filters.IsAdmin())
async def handle_help_command(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command /help from user {message.chat.id}')
    await message.answer(text=strs.admin_general_help, reply_markup=await get_menu_reply_keyboard())


@general_router.message(
    filters.Private(), filters.IsAdmin(),
    ((F.text == '/to_manager') | (F.text == 'Режим менеджера 💼'))
)
async def handle_to_manager_command(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command /to_manager from user {message.chat.id}')

    await db.users.update(
        user_id=message.chat.id,
        new_data={
            'status': 'manager'
        }
    )

    from ..managers.general import get_menu_reply_keyboard
    await message.answer(text=strs.admin_general_now_manager, reply_markup=await get_menu_reply_keyboard())
