from . import *

# __router__ !DO NOT DELETE!
ticket_data_router = Router()


# __states__ !DO NOT DELETE!
class CommentaryStates(StatesGroup):
    get_comment = State()


class ChangeTicketDataStates(StatesGroup):
    get_title = State()
    get_description = State()


# __buttons__ !DO NOT DELETE!
@ticket_data_router.callback_query(F.data.startswith('commentary_btn'))
async def handle_commentary_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling commentary commentary button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    ticket_id = data[1]

    from ..users import get_decline_reply_keyboard
    await callback.message.answer(
        text=strs.data_ask_comment,
        reply_markup=await get_decline_reply_keyboard()
    )

    await state.set_state(CommentaryStates.get_comment.state)
    await state.update_data({'ticket_id': ticket_id})

    await callback.answer()


async def _make_up_ticket_info(ticket_id: str) -> str:
    ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
    name, title, description = ticket.get('user_name'), ticket.get('title'), ticket.get('description'),
    comment = ticket.get('comment', 'Отсутствует')
    opened = str(ticket.get('open_date')).split('.')[0]
    closed = str(ticket.get('close_date', 'Отсутствует.')).split('.')[0]

    text = ''
    text += f'<b>Тикет:</b> {ticket_id}\n\n'
    text += f'<b>Создан:</b> {opened} по МСК\n\n'
    text += f'<b>Закрыт:</b> {closed} по МСК\n\n'
    text += f'<b>Имя пользователя:</b> {name}\n\n'
    text += f'<b>Тема беседы:</b> {title}\n\n'
    text += f'<b>Описание беседы:</b> {description}\n\n'
    text += f'<b>Комментарий:</b> {comment}'

    return text


@ticket_data_router.callback_query(F.data.startswith('ticket_change_data'), filters.IsManagerOrAdmin())
async def handle_ticket_data_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling ticket_history change data button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    ticket_id = data[1]

    text = await _make_up_ticket_info(ticket_id=ticket_id)
    await callback.message.answer(
        text=text,
        reply_markup=await get_ticket_change_data_inline_keyboard(ticket_id=ticket_id)
    )

    await callback.answer()


async def get_ticket_change_data_inline_keyboard(ticket_id: str) -> InlineKeyboardMarkup:
    button_list = [
        [InlineKeyboardButton(text='Изменить тему беседы 🏷️', callback_data=f'change_btn title {ticket_id}')],
        [InlineKeyboardButton(text='Изменить описание 📝', callback_data=f'change_btn description {ticket_id}')],
        [InlineKeyboardButton(text='Обновить 🔄', callback_data=f'update_btn {ticket_id}')],
        [InlineKeyboardButton(text='Закрыть 🚫', callback_data='delete_btn')],

    ]

    @ticket_data_router.callback_query(F.data.startswith('update_btn'))
    async def handle_change_title_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(
            f'Handling ticket_change_data update button callback from user {callback.message.chat.id}')
        data = callback.data.split()
        ticket_id = data[1]

        text = await _make_up_ticket_info(ticket_id=ticket_id)
        if text != callback.message.html_text:
            await callback.message.edit_text(
                text=text,
                reply_markup=await get_ticket_change_data_inline_keyboard(
                    ticket_id=ticket_id
                )
            )
        await callback.answer()

    @ticket_data_router.callback_query(F.data.startswith('change_btn'))
    async def handle_change_title_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(
            f'Handling ticket_change_data change_title button callback from user {callback.message.chat.id}')
        data = callback.data.split()
        change_var, ticket_id = data[1], data[2]

        from ..users import get_decline_reply_keyboard
        if change_var == 'title':
            await callback.message.answer(
                text=strs.ticket_ask_title,
                reply_markup=await get_decline_reply_keyboard()
            )
            await state.set_state(ChangeTicketDataStates.get_title.state)
        else:
            await callback.message.answer(
                text=strs.ticket_ask_description,
                reply_markup=await get_decline_reply_keyboard()
            )
            await state.set_state(ChangeTicketDataStates.get_description.state)
        await state.update_data({'ticket_id': ticket_id})

        await callback.answer()

    @ticket_data_router.callback_query(F.data.startswith('delete_btn'))
    async def handle_close_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling ticket_change_data close button callback from user {callback.message.chat.id}')
        await callback.message.delete()
        await callback.answer()

    return InlineKeyboardMarkup(inline_keyboard=button_list)


# __chat__ !DO NOT DELETE!
@ticket_data_router.message(CommentaryStates.get_comment)
async def handle_get_comment_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states CommentaryStates.get_comment from user {message.chat.id}')
    comment = message.text
    if comment and len(comment) < 100:
        data = await state.get_data()
        ticket_id = data['ticket_id']

        await db.tickets.update(
            ticket_id=ticket_id,
            new_data={
                'comment': comment
            }
        )

        from .general import get_menu_reply_keyboard
        await message.answer(text=strs.data_update, reply_markup=await get_menu_reply_keyboard())

        await state.clear()
    else:
        await message.answer(text=strs.data_ask_comment_error)


@ticket_data_router.message(ChangeTicketDataStates.get_title)
async def handle_get_title_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states ChangeTicketDataStates.get_title from user {message.chat.id}')
    title = message.text
    if title and len(title) < 50:
        data = await state.get_data()
        ticket_id = data['ticket_id']

        await db.tickets.update(
            ticket_id=ticket_id,
            new_data={
                'title': title
            }
        )

        ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
        user_id = ticket.get('user_id')
        await message.bot.send_message(
            chat_id=user_id,
            text=strs.data_title_changed(title=title)
        )

        from .general import get_menu_reply_keyboard
        await message.answer(text=strs.data_update, reply_markup=await get_menu_reply_keyboard())
        await state.clear()
    else:
        await message.answer(text=strs.ticket_ask_title_error)


@ticket_data_router.message(ChangeTicketDataStates.get_description)
async def handle_get_description_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states ChangeTicketDataStates.get_description from user {message.chat.id}')
    description = message.text
    if description and len(description) < 50:
        data = await state.get_data()
        ticket_id = data['ticket_id']

        await db.tickets.update(
            ticket_id=ticket_id,
            new_data={
                'description': description
            }
        )

        ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
        user_id = ticket.get('user_id')
        await message.bot.send_message(
            chat_id=user_id,
            text=strs.data_description_changed(description=description)
        )

        from .general import get_menu_reply_keyboard
        await message.answer(text=strs.data_update, reply_markup=await get_menu_reply_keyboard())
        await state.clear()
    else:
        await message.answer(text=strs.ticket_ask_description_error)
