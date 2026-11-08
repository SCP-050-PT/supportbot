from . import *

# Standard
from datetime import datetime, timezone, timedelta
from json import dumps, loads
import os

# Project
import handlers.utils as utils

# __router__ !DO NOT DELETE!
ticket_router = Router()


# __states__ !DO NOT DELETE!


# __buttons__ !DO NOT DELETE!
@ticket_router.callback_query(F.data.startswith('delete_btn'), filters.IsManagerOrAdmin())
async def handle_media_close_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling media_menu media_close button callback from user {callback.message.chat.id}')
    await callback.message.delete()
    await callback.message.answer(text=strs.use_help)
    await callback.answer()


async def get_accept_ticket_inline_keyboard(ticket_id: str) -> InlineKeyboardMarkup:
    button_list = [
        [InlineKeyboardButton(text='Принять ✅', callback_data=f'accept_btn {ticket_id}')],
        [InlineKeyboardButton(text='Спрятать 🗂️', callback_data='hide_btn')],
    ]

    @ticket_router.callback_query(F.data.startswith('accept_btn'), filters.IsManagerOrAdmin())
    async def handle_accept_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling accept_ticket accept button callback from user {callback.message.chat.id}')
        data = callback.data.split()
        ticket_id = data[1]

        ticket = await db.tickets.get_by_id(ticket_id)
        close_date = ticket.get('close_date')
        if close_date:
            await callback.answer(text=strs.ticket_already_closed, show_alert=True)
            await callback.message.delete()
            return

        manager = await db.users.get_by_id(user_id=callback.message.chat.id)
        current_ticket_id = manager.get('current_ticket_id')
        if current_ticket_id:
            await callback.answer(text=strs.ticket_already_have_current, show_alert=True)
            return

        current_date = str(datetime.now(timezone(timedelta(hours=3))))
        await db.tickets.update(
            ticket_id=ticket_id,
            new_data={
                'manager_id': callback.message.chat.id,
                'last_modified': current_date,
            }
        )

        await db.users.update(
            user_id=callback.message.chat.id,
            new_data={
                'current_ticket_id': ticket_id
            }
        )

        ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
        await callback.bot.send_message(
            chat_id=ticket.get('user_id'),
            text=strs.ticket_accepted_manager
        )

        await callback.message.delete()
        await callback.message.answer(text=strs.ticket_accepted)

        await callback.answer()

    @ticket_router.callback_query(F.data.startswith('hide_btn'), filters.IsManagerOrAdmin())
    async def handle_hide_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling accept_ticket hide button callback from user {callback.message.chat.id}')
        await callback.message.delete()
        await callback.answer()

    return InlineKeyboardMarkup(inline_keyboard=button_list)


async def get_media_menu_inline_keyboard(ticket_page: int, ticket_id: str, page: int) -> InlineKeyboardMarkup:
    button_list = [
        [InlineKeyboardButton(text='⏪', callback_data=f'media_prev_btn {ticket_id} {ticket_page} {page}'),
         InlineKeyboardButton(text='⏩', callback_data=f'media_next_btn {ticket_id} {ticket_page} {page}')],
        [InlineKeyboardButton(text='Закрыть 🚫', callback_data='delete_btn')],
    ]

    @ticket_router.callback_query(F.data.startswith('media_prev_btn'), filters.IsManagerOrAdmin())
    async def handle_media_prev_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling media_menu media_prev button callback from user {callback.message.chat.id}')
        data = callback.data.split()
        ticket_id, ticket_page, page = data[1], int(data[2]), int(data[3])

        ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
        messages = await utils.get_media_messages(page=ticket_page, ticket=ticket)

        prev_page = page
        page = page - 1 if page != 1 else len(messages)
        if page != prev_page:
            current_message = messages[page - 1]
            await callback.message.delete()
            await current_message.send_copy(
                chat_id=callback.message.chat.id,
                reply_markup=await get_media_menu_inline_keyboard(
                    ticket_page=ticket_page, ticket_id=ticket_id, page=page
                ),
                parse_mode='html'
            ).as_(callback.bot)

        await callback.answer()

    @ticket_router.callback_query(F.data.startswith('media_next_btn'), filters.IsManagerOrAdmin())
    async def handle_media_next_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling media_menu media_next button callback from user {callback.message.chat.id}')
        data = callback.data.split()
        ticket_id, ticket_page, page = data[1], int(data[2]), int(data[3])

        ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
        messages = await utils.get_media_messages(page=ticket_page, ticket=ticket)

        prev_page = page
        page = page + 1 if page != len(messages) else 1
        if page != prev_page:
            current_message = messages[page - 1]
            await callback.message.delete()
            await current_message.send_copy(
                chat_id=callback.message.chat.id,
                reply_markup=await get_media_menu_inline_keyboard(
                    ticket_page=ticket_page, ticket_id=ticket_id, page=page
                ),
                parse_mode='html'
            ).as_(callback.bot)

        await callback.answer()

    return InlineKeyboardMarkup(inline_keyboard=button_list)


async def get_archive_menu_inline_keyboard(tickets: list[dict], page: int, user_id: int,
                                           is_manager: bool) -> InlineKeyboardMarkup:
    button_list = []

    from math import ceil
    max_pages = ceil(len(tickets) / utils.BATCH)

    upper = page * utils.BATCH if len(tickets) > page * utils.BATCH else len(tickets)
    lower = upper - utils.BATCH if upper - utils.BATCH >= 0 else 0
    if tickets:
        for i in range(lower, upper):
            ticket = tickets[i]
            ticket_id = ticket.get('ticket_id')
            button_list.append(
                [InlineKeyboardButton(text=f'Тикет {ticket_id}',
                                      callback_data=f'archive_ticket_btn {ticket_id} {page} {user_id} {int(is_manager)}')])

    button_list.append(
        [InlineKeyboardButton(text='⏪',
                              callback_data=f'archive_prev_btn {page} {max_pages} {user_id} {int(is_manager)}'),
         InlineKeyboardButton(text='⏩',
                              callback_data=f'archive_next_btn {page} {max_pages} {user_id} {int(is_manager)}')]
    )
    if is_manager:
        button_list.append(
            [InlineKeyboardButton(text='🔙 Вернуться назад',
                                  callback_data=f'archive_back_btn {user_id} {int(is_manager)}')]
        )
    else:
        button_list.append(
            [InlineKeyboardButton(text='Закрыть 🚫', callback_data='delete_btn')]
        )

    @ticket_router.callback_query(F.data.startswith('archive_ticket_btn'), filters.IsManagerOrAdmin())
    async def handle_ticket_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling archive_menu ticket button callback from user {callback.message.chat.id}')
        data = callback.data.split()
        ticket_id, page, user_id, is_manager = data[1], int(data[2]), int(data[3]), bool(int(data[4]))

        ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
        content = ticket.get('content')
        content = content if content else []

        ticket_text = await utils.make_up_ticket_page_text(page=1, content=content, ticket=ticket, extended_info=True)
        await callback.message.edit_text(
            text=ticket_text,
            reply_markup=await get_ticket_history_inline_keyboard(
                ticket_id=ticket_id, page=1, user_id=user_id, is_manager=is_manager,
                back_data=f'history_back_l_btn {page} {user_id} {int(is_manager)}'
            )
        )

        await callback.answer()

    @ticket_router.callback_query(F.data.startswith(('archive_prev_btn', 'archive_next_btn')),
                                  filters.IsManagerOrAdmin())
    async def handle_page_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling archive_menu page button callback from user {callback.message.chat.id}')
        data = callback.data.split()
        page, max_pages, user_id, is_manager = int(data[1]), int(data[2]), int(data[3]), bool(int(data[4]))
        direction = data[0].split('_')[1]

        prev_page = page
        if direction == 'next':
            page = page + 1 if page < max_pages else 1
        elif direction == 'prev':
            page = page - 1 if page > 1 else max_pages

        tickets = await db.tickets.get_all_by_id(user_id=user_id, is_manager=is_manager)
        text = await utils.make_up_tickets_info_page(page=page, tickets=tickets, is_extended=is_manager)

        if page != prev_page:
            await callback.message.edit_text(
                text=text,
                reply_markup=await get_archive_menu_inline_keyboard(
                    tickets=tickets, page=page, user_id=user_id, is_manager=is_manager
                )
            )
        await callback.answer()

    @ticket_router.callback_query(F.data.startswith('archive_back_btn'), filters.IsManagerOrAdmin())
    async def handle_back_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling archive_menu back button callback from user {callback.message.chat.id}')
        data = callback.data.split()
        # Parse the incoming callback data
        user_id, is_manager = int(data[1]), bool(int(data[2]))

        # The rest of the code remains the same...
        user = await db.users.get_by_id(user_id=user_id)  # Use the parsed user_id here
        current_ticket_id = user.get('current_ticket_id')
        ticket = None
        ticket_info = strs.ticket_no_opened
        if current_ticket_id:
            ticket = await db.tickets.get_by_id(ticket_id=current_ticket_id)
            if ticket:
                name, title, description = ticket.get('user_name'), ticket.get('title'), ticket.get('description')
                tg_id, tg_name = user.get('user_id'), user.get('user_name')
                ticket_info = strs.ticket_info(
                    id_=tg_id, tg_name=tg_name,
                    name=name, title=title, description=description
                )
        ticket_id = None if not ticket else ticket.get('ticket_id')
        is_current = True if current_ticket_id else False

        # Ensure that get_ticket_menu_inline_keyboard function is updated to accept and handle
        # the is_manager parameter if required by your implementation...
        await callback.message.edit_text(
            text=ticket_info,
            reply_markup=await get_ticket_menu_inline_keyboard(
                ticket_id=ticket_id,
                is_current=is_current
                # Add is_manager here if needed, depending on function signature
            )
        )

        await callback.answer()

    return InlineKeyboardMarkup(inline_keyboard=button_list)


@ticket_router.callback_query(F.data.startswith('ticket_user_tickets'), filters.IsManagerOrAdmin())
async def handle_user_tickets_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling ticket_history prev button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    user_id = ticket_id = None
    is_manager = False
    if len(data) == 2:
        ticket_id = data[1]
    if len(data) == 4:
        ticket_id, user_id, is_manager = data[1], int(data[2]), bool(int(data[3]))

    if not user_id:
        ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
        user_id = ticket.get('user_id')

    tickets = await db.tickets.get_all_by_id(user_id=user_id, is_manager=is_manager)
    if tickets:
        text = await utils.make_up_tickets_info_page(page=1, tickets=tickets, is_extended=is_manager)
        await callback.message.answer(
            text=text,
            reply_markup=await get_archive_menu_inline_keyboard(
                tickets=tickets, page=1, user_id=user_id, is_manager=is_manager
            )
        )

    await callback.answer()


async def get_ticket_history_inline_keyboard(
        ticket_id: str, page: int, user_id: int = None, is_manager: bool = True,
        back_data: str = 'history_back_my_btn'
) -> InlineKeyboardMarkup:
    button_list = [
        [InlineKeyboardButton(text='⏪',
                              callback_data=f'history_prev_btn {ticket_id} {page} {user_id} {int(is_manager)}'),
         InlineKeyboardButton(text='📥', callback_data=f'history_open_media_btn {ticket_id} {page}'),
         InlineKeyboardButton(text='⏩',
                              callback_data=f'history_next_btn {ticket_id} {page} {user_id} {int(is_manager)}')],
    ]
    if is_manager:
        button_list.extend([
            [InlineKeyboardButton(text='Информация о пользователе ℹ️', callback_data=f'ticket_user_info {ticket_id}')]
        ])
    button_list.append([
        InlineKeyboardButton(
            text='🔙 Вернуться назад', callback_data=f'history_back_l_btn 1 {user_id} {int(is_manager)}'
        ),
    ])

    async def handle_ticket_pagination_callback(
            callback: CallbackQuery, direction: str, state: FSMContext
    ):
        bot_logger.info(f'Handling ticket_history {direction} button callback from user {callback.message.chat.id}')

        data = callback.data.split()
        user_id = int(data[3]) if data[3].isdigit() else None
        ticket_id, page, is_manager = data[1], int(data[2]), bool(int(data[4]))

        ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
        content = ticket.get('content', [])

        from math import ceil
        max_pages = ceil(len(content) / utils.BATCH)
        if direction == 'prev':
            new_page = page - 1 if page > 1 else max_pages
        else:
            new_page = page + 1 if page < max_pages else 1

        if page != new_page:
            user = await db.users.get_by_id(user_id=callback.message.chat.id)
            current_ticket_id = user.get('current_ticket_id')
            back_data = 'history_back_my_btn' if current_ticket_id else f'history_back_l_btn 1 {user_id} {int(is_manager)}'

            ticket_text = await utils.make_up_ticket_page_text(
                page=new_page, content=content, ticket=ticket, extended_info=True
            )

            await callback.message.edit_text(
                text=ticket_text,
                reply_markup=await get_ticket_history_inline_keyboard(
                    ticket_id=ticket_id, page=new_page, user_id=user_id, is_manager=is_manager,
                    back_data=back_data
                )
            )

        await callback.answer()

    @ticket_router.callback_query(F.data.startswith('history_prev_btn'), filters.IsManagerOrAdmin())
    async def handle_prev_button_callback(callback: CallbackQuery, state: FSMContext):
        await handle_ticket_pagination_callback(callback, 'prev', state)

    @ticket_router.callback_query(F.data.startswith('history_next_btn'), filters.IsManagerOrAdmin())
    async def handle_next_button_callback(callback: CallbackQuery, state: FSMContext):
        await handle_ticket_pagination_callback(callback, 'next', state)

    @ticket_router.callback_query(F.data.startswith('ticket_user_info'), filters.IsManagerOrAdmin())
    async def handle_user_info_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling ticket_history user_info button callback from user {callback.message.chat.id}')
        data = callback.data.split()
        ticket_id = data[1]

        ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
        user_id = ticket.get('user_id')
        user = await db.users.get_by_id(user_id=user_id)

        from .user_search import get_user_actions_inline_keyboard
        if user:
            cur_user = await db.users.get_by_id(user_id=callback.message.chat.id)
            is_user_admin = cur_user.get('status') == 'admin'
            is_manager, info = await utils.make_up_user_info(user=user)
            await callback.message.answer(text=info, reply_markup=await get_user_actions_inline_keyboard(
                ticket_id=user.get('current_ticket_id'), user_id=int(user.get('user_id')),
                user_is_manager=is_manager, is_user_admin=is_user_admin
            ))

        await callback.answer()

    @ticket_router.callback_query(F.data.startswith('history_open_media_btn'), filters.IsManagerOrAdmin())
    async def handle_open_media_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling ticket_history open_media button callback from user {callback.message.chat.id}')
        data = callback.data.split()
        ticket_id, page = data[1], int(data[2])

        ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
        messages = await utils.get_media_messages(page=page, ticket=ticket)
        if messages:
            current_message = messages[0]
            await current_message.send_copy(
                chat_id=callback.message.chat.id,
                reply_markup=await get_media_menu_inline_keyboard(
                    ticket_page=page, ticket_id=ticket_id, page=1
                ),
                parse_mode='html'
            ).as_(callback.bot)
        else:
            await callback.answer(text=strs.ticket_no_media_on_page, show_alert=True)

        await callback.answer()

    @ticket_router.callback_query(F.data.startswith('history_back_my_btn'), filters.IsManagerOrAdmin())
    async def handle_back_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(
            f'Handling ticket_history back to my tickets menu button callback from user {callback.message.chat.id}')

        user = await db.users.get_by_id(user_id=callback.message.chat.id)
        current_ticket_id = user.get('current_ticket_id')

        text = strs.ticket_no_opened
        ticket = None
        is_current = False
        if current_ticket_id:
            is_current = True
            ticket = await db.tickets.get_by_id(ticket_id=current_ticket_id)
            name, title, description = ticket.get('user_name'), ticket.get('title'), ticket.get('description')
            ticket_user = await db.users.get_by_id(user_id=ticket.get('user_id'))
            tg_id, tg_name = ticket_user.get('user_id'), ticket_user.get('user_name')
            ticket_info = strs.ticket_info(
                id_=tg_id, tg_name=tg_name,
                name=name, title=title, description=description
            )
            comment = ticket.get('comment')
            comment = comment if comment or comment != 'None' else 'Отсутствует'
            text = '<b>Текущий тикет:</b>\n\n' + ticket_info + '\n\n<b>Комментарий: </b>' + comment

        await callback.message.edit_text(
            text=text,
            reply_markup=await get_ticket_menu_inline_keyboard(
                is_current=is_current,
                ticket_id=None if not ticket else ticket.get('ticket_id')
            )
        )
        await callback.answer()

    @ticket_router.callback_query(F.data.startswith('history_back_l_btn'), filters.IsManagerOrAdmin())
    async def handle_back_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling ticket_history back to list button callback from user {callback.message.chat.id}')
        data = callback.data.split()
        user_id = int(data[2]) if data[2].isdigit() else None
        page, is_manager = int(data[1]), bool(int(data[3]))

        if not user_id:
            user_id = callback.message.chat.id

        tickets = await db.tickets.get_all_by_id(user_id=user_id, is_manager=is_manager)
        text = await utils.make_up_tickets_info_page(page=page, tickets=tickets, is_extended=is_manager)
        await callback.message.edit_text(
            text=text,
            reply_markup=await get_archive_menu_inline_keyboard(
                tickets=tickets, page=page, user_id=user_id, is_manager=is_manager
            )
        )

        await callback.answer()

    return InlineKeyboardMarkup(inline_keyboard=button_list)


async def get_ticket_menu_inline_keyboard(
        ticket_id: str | None = None,
        is_current: bool = False
) -> InlineKeyboardMarkup:
    button_list = []
    if is_current:
        button_list = [
            [InlineKeyboardButton(text='Закрыть 🚫', callback_data=f'close_btn {ticket_id}'),
             InlineKeyboardButton(text='Ограничить 🤐', callback_data=f'ticket_mute {ticket_id}')],
            [InlineKeyboardButton(text='История 💬', callback_data=f'history_btn {ticket_id}'),
             InlineKeyboardButton(text='Комментарий ✍', callback_data=f'commentary_btn {ticket_id}')],
            [InlineKeyboardButton(text='Данные беседы 🔄', callback_data=f'ticket_change_data {ticket_id}'),
             InlineKeyboardButton(text='Освободить 🙅🏻‍♂️', callback_data=f'ticket_release {ticket_id}')]
        ]
    button_list.append([InlineKeyboardButton(text='Архив 🗄️', callback_data='archive_btn')], )

    @ticket_router.callback_query(F.data.startswith('ticket_release'), filters.IsManagerOrAdmin())
    async def handle_release_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling ticket_menu release button callback from user {callback.message.chat.id}')
        data = callback.data.split()
        ticket_id = data[1]

        await db.tickets.update(
            ticket_id=ticket_id,
            new_data={
                'manager_id': None
            }
        )

        await db.users.update(
            user_id=callback.message.chat.id,
            new_data={
                'current_ticket_id': None
            }
        )

        managers = await db.users.get_all_managers()
        ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
        if managers:
            user = await db.users.get_by_id(user_id=ticket.get('user_id'))
            name, title, description = ticket.get('user_name'), ticket.get('title'), ticket.get('description')
            ticket_user = await db.users.get_by_id(user_id=ticket.get('user_id'))
            tg_id, tg_name = ticket_user.get('user_id'), ticket_user.get('user_name')
            ticket_info = strs.ticket_info(
                id_=tg_id, tg_name=tg_name,
                name=name, title=title, description=description
            )
            for manager in managers:
                manager_id = manager.get('user_id')
                if manager_id != callback.message.chat.id:
                    await callback.bot.send_message(
                        chat_id=manager_id,
                        text='<b>Менеджер освободил тикет!</b>\n\n' + ticket_info,
                        reply_markup=await get_accept_ticket_inline_keyboard(
                            ticket_id=ticket_id
                        )
                    )

        await callback.bot.send_message(
            chat_id=ticket.get('user_id'),
            text=strs.ticket_manager_released
        )

        await callback.answer(text=strs.ticket_released, show_alert=True)
        await callback.message.delete()

        await callback.answer()

    @ticket_router.callback_query(F.data.startswith('close_btn'), filters.IsManagerOrAdmin())
    async def handle_close_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling ticket_menu close button callback from user {callback.message.chat.id}')
        data = callback.data.split()
        ticket_id_ = data[1]
        ticket = await db.tickets.get_by_id(ticket_id=ticket_id_)
        if ticket:
            current_date = str(datetime.now(timezone(timedelta(hours=3))))
            await db.tickets.update(
                ticket_id=ticket_id_,
                new_data={
                    'close_date': current_date,
                    'last_modified': current_date,
                }
            )
            await db.users.update(
                user_id=callback.message.chat.id,
                new_data={
                    'current_ticket_id': None
                }
            )
            user_id = ticket.get('user_id')
            if user_id:
                ticket_info = strs.ticket_closed_by_manager(
                    name=ticket.get('user_name'), title=ticket.get('title'), description=ticket.get('description')
                )
                await callback.bot.send_message(
                    chat_id=user_id,
                    text=ticket_info
                )
                await db.users.update(
                    user_id=user_id,
                    new_data={
                        'current_ticket_id': None
                    }
                )

            await callback.message.edit_text(
                text=strs.ticket_no_opened_manager,
                reply_markup=await get_ticket_menu_inline_keyboard(is_current=False)
            )
        await callback.answer()

    @ticket_router.callback_query(F.data.startswith('history_btn'), filters.IsManagerOrAdmin())
    async def handle_history_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling ticket_menu history button callback from user {callback.message.chat.id}')
        user = await db.users.get_by_id(user_id=callback.message.chat.id)
        current_ticket = await db.tickets.get_by_id(user.get('current_ticket_id'))
        content = current_ticket.get('content')
        if content:
            ticket_text = await utils.make_up_ticket_page_text(
                page=1, content=content,
                ticket=current_ticket, extended_info=True
            )
            await callback.message.edit_text(
                text=ticket_text,
                reply_markup=await get_ticket_history_inline_keyboard(
                    ticket_id=ticket_id,
                    page=1,
                )
            )
        else:
            await callback.message.answer(text=strs.ticket_no_history)
        await callback.answer()

    @ticket_router.callback_query(F.data.startswith('archive_btn'), filters.IsManagerOrAdmin())
    async def handle_archive_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling ticket_menu archive button callback from user {callback.message.chat.id}')
        tickets = await db.tickets.get_all_by_id(user_id=callback.message.chat.id, is_manager=True)

        if tickets:
            text = await utils.make_up_tickets_info_page(page=1, tickets=tickets, is_extended=True)
            await callback.message.edit_text(
                text=text,
                reply_markup=await get_archive_menu_inline_keyboard(
                    tickets=tickets, page=1, user_id=callback.message.chat.id, is_manager=True
                )
            )
        else:
            await callback.answer(text=strs.tickets_no_archive, show_alert=True)

        await callback.answer()

    return InlineKeyboardMarkup(inline_keyboard=button_list)


# __chat__ !DO NOT DELETE!
@ticket_router.message(
    filters.Private(), filters.IsManagerOrAdmin(),
    ((F.text == '/my_tickets') | (F.text == 'Мои тикеты 📂')),
    filters.IsRestricted()
)
async def handle_my_tickets_command(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command /my_tickets from user {message.chat.id}')
    user = await db.users.get_by_id(user_id=message.chat.id)
    current_ticket_id = user.get('current_ticket_id')
    if current_ticket_id:
        ticket = await db.tickets.get_by_id(ticket_id=current_ticket_id)
        if ticket:
            name, title, description = ticket.get('user_name'), ticket.get('title'), ticket.get('description')
            ticket_user = await db.users.get_by_id(user_id=ticket.get('user_id'))
            tg_id, tg_name = ticket_user.get('user_id'), ticket_user.get('user_name')
            ticket_info = strs.ticket_info(
                id_=tg_id, tg_name=tg_name,
                name=name, title=title, description=description
            )
            comment = ticket.get('comment')
            comment = comment if comment else 'Отсутствует'
            text = '<b>Текущий тикет:</b>\n\n' + ticket_info + '\n\n<b>Комментарий: </b>' + comment
            await message.answer(
                text=text,
                reply_markup=await get_ticket_menu_inline_keyboard(is_current=True, ticket_id=ticket.get('ticket_id'))
            )
            return

    await message.answer(
        text=strs.ticket_no_opened_manager,
        reply_markup=await get_ticket_menu_inline_keyboard(is_current=False)
    )


@ticket_router.message(
    filters.Private(), filters.IsManagerOrAdmin(),
    ((F.text == '/opened_tickets') | (F.text == 'Открытые беседы 💬')),
    filters.IsRestricted()
)
async def handle_show_opened_tickets_command(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command /opened_tickets from user {message.chat.id}')
    opened_tickets = await db.tickets.get_all_opened()
    if opened_tickets:
        for ticket in opened_tickets:
            ticket_id = ticket.get('ticket_id')
            name, title, description = ticket.get('user_name'), ticket.get('title'), ticket.get('description')
            ticket_user = await db.users.get_by_id(user_id=ticket.get('user_id'))
            tg_id, tg_name = ticket_user.get('user_id'), ticket_user.get('user_name')
            ticket_info = strs.ticket_info(
                id_=tg_id, tg_name=tg_name,
                name=name, title=title, description=description
            )
            await message.answer(
                text=ticket_info,
                reply_markup=await get_accept_ticket_inline_keyboard(ticket_id=ticket_id)
            )
    else:
        await message.answer(text=strs.ticket_no_opened_tickets)


@ticket_router.message(
    filters.Private(), filters.IsManagerOrAdmin(), filters.InTicket(),
    filters.NotInState(), filters.IsRestricted()
)
async def handle_user_ticket_message(message: Message, state: FSMContext):
    bot_logger.info(f'Handling user ticket message of user {message.chat.id}')
    manager = await db.users.get_by_id(user_id=message.chat.id)
    current_ticket_id = manager.get('current_ticket_id')
    ticket = await db.tickets.get_by_id(ticket_id=current_ticket_id)

    user_id = ticket.get('user_id')
    await message.send_copy(chat_id=user_id).as_(message.bot)

    from handlers.utils import CustomJSONEncoder
    current_date = str(datetime.now(timezone(timedelta(hours=3))))
    content = ticket.get('content') if ticket.get('content') else []
    message_info = loads(dumps(message.model_dump(), cls=CustomJSONEncoder))
    content.append(message_info)
    await db.tickets.update(
        ticket_id=current_ticket_id,
        new_data={
            'last_modified': current_date,
            'content': content
        }
    )

    if not message.text:
        media = (message.photo or message.video or message.audio or message.document or message.sticker
                 or message.voice or message.video_note or message.story or message.contact)
        if media:
            media_id = media[-1].file_id if isinstance(media, list) else media.file_id
            file_info = await message.bot.get_file(file_id=media_id)
            file_path = file_info.file_path
            media_url = f'https://api.telegram.org/file/bot{cf.bot["token"]}/{file_path}'

            destination_folder = cf.project['storage'] + f'/{ticket.get("ticket_id")}'
            os.makedirs(destination_folder, exist_ok=True)

            media_info = f'{message.message_id} {message.media_group_id} {media_url}'
            with open(f'{destination_folder}/media_info.txt', 'a', encoding='utf-16') as f:
                f.write(media_info + '\n')
        else:
            bot_logger.warning('Do not support this type of message!')
