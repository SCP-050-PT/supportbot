from . import *

# Standard
from datetime import datetime, timezone, timedelta

# __router__ !DO NOT DELETE!
mute_router = Router()


# __states__ !DO NOT DELETE!
class MuteStates(StatesGroup):
    get_mute_time = State()


# __buttons__ !DO NOT DELETE!
async def _close_ticket(ticket_id: str):
    ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
    if ticket:
        current_date = str(datetime.now(timezone(timedelta(hours=3))))
        close_date = ticket.get('close_date')
        manager_id = ticket.get('manager_id')
        if not close_date:
            await db.tickets.update(
                ticket_id=ticket_id,
                new_data={
                    'close_date': current_date,
                    'last_modified': current_date,
                }
            )
            if manager_id:
                await db.users.update(
                    user_id=manager_id,
                    new_data={
                        'current_ticket_id': None
                    }
                )
            user_id = ticket.get('user_id')
            if user_id:
                await db.users.update(
                    user_id=user_id,
                    new_data={
                        'current_ticket_id': None
                    }
                )


@mute_router.callback_query(F.data.startswith('ban_btn'))
async def handle_ban_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling user_actions ban button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    user_id, ticket_id = int(data[1]), data[2]

    if ticket_id:
        await _close_ticket(ticket_id=ticket_id)

    await db.users.update(
        user_id=user_id,
        new_data={
            'is_banned': True
        }
    )

    await callback.bot.send_message(
        chat_id=user_id,
        text=strs.restriction_banned_forever
    )

    await callback.answer(text=strs.restriction_banned_successfully + ' Нажмите на кнопку "Обновить 🔄"',
                          show_alert=True)
    await callback.answer()


@mute_router.callback_query(F.data.startswith('unban_btn'))
async def handle_ban_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling user_actions ban button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    user_id = int(data[1])

    await db.users.update(
        user_id=user_id,
        new_data={
            'is_banned': False
        }
    )

    await callback.bot.send_message(
        chat_id=user_id,
        text=strs.restriction_unbanned
    )

    await callback.answer(text=strs.restriction_unbanned_successfully + ' Нажмите на кнопку "Обновить 🔄"',
                          show_alert=True)
    await callback.answer()


@mute_router.callback_query(F.data.startswith('ticket_mute'), filters.IsManagerOrAdmin())
async def handle_mute_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling ticket_menu mute button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    user_id = ticket_id = None
    if len(data) == 2:
        ticket_id = data[1]
    elif len(data) == 3:
        ticket_id, user_id = data[1], int(data[2])

    from ..users import get_decline_reply_keyboard
    await callback.message.answer(text=strs.ticket_get_mute, reply_markup=await get_decline_reply_keyboard())

    await state.update_data({'ticket_id': ticket_id, 'user_id': user_id})
    await state.set_state(MuteStates.get_mute_time.state)

    await callback.answer()


# __chat__ !DO NOT DELETE!
@ticket_router.message(MuteStates.get_mute_time)
async def handle_get_mute_time_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states MuteStates.get_mute_time from user {message.chat.id}')
    mute_mins = message.text
    if mute_mins and mute_mins.isdigit() and 0 <= int(mute_mins) <= 1440:
        data = await state.get_data()
        ticket_id = data['ticket_id']
        user_id = data['user_id']

        if int(mute_mins) == 0:
            await db.users.update(
                user_id=user_id,
                new_data={'mute_time': None}
            )

            await message.bot.send_message(
                chat_id=user_id,
                text=strs.restriction_unmuted
            )

            from .general import get_menu_reply_keyboard
            await message.answer(
                text=strs.restriction_unmuted_succesfully,
                reply_markup=await get_menu_reply_keyboard()
            )

            await state.clear()
            return

        if ticket_id != 'None':
            ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
            await _close_ticket(ticket_id=ticket_id)
            user_id = ticket.get('user_id')

        current_time = datetime.now(timezone(timedelta(hours=3)))
        await db.users.update(
            user_id=user_id,
            new_data={
                'mute_time': str(current_time + timedelta(minutes=int(mute_mins)))
            }
        )

        await message.bot.send_message(
            chat_id=user_id,
            text=strs.restirction_get_muted(mute_mins)
        )

        from .general import get_menu_reply_keyboard
        await message.answer(
            text=strs.restriction_succesfully(mute_mins),
            reply_markup=await get_menu_reply_keyboard()
        )

        await state.clear()
    else:
        await message.answer(text=strs.ticket_get_mute_error)
