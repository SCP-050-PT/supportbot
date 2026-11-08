# Standard
from datetime import datetime, timezone, timedelta

# Project
from database import db
from logger import background_logger
from bot import bot
from resources import strings as strs


async def release_check():
    background_logger.warning('Starting one than one hour last modified tickets check')
    release = await db.preferences.get_by_key('release_hours')
    hours_ago = int(release.get('value'))
    more_than_hours_tickets = await db.tickets.get_tickets_last_modified_ago(hours_ago=hours_ago)
    if more_than_hours_tickets:
        for ticket in more_than_hours_tickets:
            ticket_manager_id = ticket.get('manager_id')
            if not ticket_manager_id or ticket_manager_id == 'None':
                continue

            ticket_id = ticket.get('ticket_id')

            await db.tickets.update(
                ticket_id=ticket_id,
                new_data={
                    'manager_id': None
                }
            )

            await db.users.update(
                user_id=ticket_manager_id,
                new_data={
                    'current_ticket_id': None
                }
            )

            managers = await db.users.get_all_managers()
            if managers:
                user = await db.users.get_by_id(user_id=ticket.get('user_id'))
                name, title, description = ticket.get('user_name'), ticket.get('title'), ticket.get('description')
                tg_id, tg_name = user.get('user_id'), user.get('user_name')
                ticket_info = strs.ticket_info(
                    id_=tg_id, tg_name=tg_name,
                    name=name, title=title, description=description
                )
                for manager in managers:
                    from ..private.managers.tickets import get_accept_ticket_inline_keyboard
                    manager_id = manager.get('user_id')
                    if manager_id != ticket_manager_id:
                        await bot.send_message(
                            chat_id=manager_id,
                            text='<b>Беседа не обновляется более часа! Перенаправление свободным менеджерам</b>\n\n' + ticket_info,
                            reply_markup=await get_accept_ticket_inline_keyboard(
                                ticket_id=ticket_id
                            )
                        )
                    else:
                        await bot.send_message(
                            chat_id=manager_id,
                            text=strs.last_modified_manager_disconnected(time=hours_ago),
                        )


async def close_check():
    background_logger.warning('Starting one than thirty six hours last modified tickets check')
    close = await db.preferences.get_by_key('close_hours')
    hours_ago = int(close.get('value'))
    more_than_hours_tickets = await db.tickets.get_tickets_last_modified_ago(hours_ago=hours_ago)
    if more_than_hours_tickets:
        current_date = str(datetime.now(timezone(timedelta(hours=3))))
        for ticket in more_than_hours_tickets:
            ticket_id = ticket.get('ticket_id')

            await db.tickets.update(
                ticket_id=ticket_id,
                new_data={
                    'close_date': current_date,
                    'last_modified': current_date,
                }
            )

            ticket_manager_id = ticket.get('manager_id')
            if ticket_manager_id and ticket_manager_id != 'None':
                await db.users.update(
                    user_id=ticket_manager_id,
                    new_data={
                        'current_ticket_id': None
                    }
                )

                await bot.send_message(
                    chat_id=ticket_manager_id,
                    text=strs.last_modified_outdated(time=hours_ago)
                )

            user_id = ticket.get('user_id')
            await db.users.update(
                user_id=user_id,
                new_data={
                    'current_ticket_id': None
                }
            )

            await bot.send_message(
                chat_id=user_id,
                text=strs.last_modified_outdated(time=hours_ago)
            )
