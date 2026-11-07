# Third-party
from aiogram.types import Message

# Standard
from datetime import datetime
from json import JSONEncoder
from database import db
import os

# Project
import config as cf

BATCH = 3


# Custom JSON Encoder that handles datetime objects
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return JSONEncoder.default(self, obj)


async def make_up_ticket_page_text(page: int, content: list, ticket: dict, extended_info: bool = False) -> str:
    upper = page * BATCH if len(content) > page * BATCH else len(content)
    lower = upper - BATCH if upper - BATCH >= 0 else 0
    message_text = f'<i>История: Тикет {ticket.get("ticket_id")}</i> <b>|{upper}/{len(content)}|</b>\n\n'
    for i in range(lower, upper):
        message_info = content[i]
        message = Message(**message_info)
        media_group_id = message_info.get('media_group_id')
        media_group_text = media_group_id if media_group_id else 'Отсутствует'
        user_id = message_info.get('chat').get('id')
        manager_id = ticket.get('manager_id')
        text = message.html_text
        msg_caption = message_info.get('caption')
        is_manager = manager_id == user_id if manager_id else False

        message_id = message_info.get('message_id')

        manager_info = user_info = None
        if extended_info:
            if is_manager:
                manager_id = ticket.get('manager_id')
                manager_info = f'<b>🗣️ Менеджер: ({manager_id})</b>\nID сообщения: {message_id}\nМедиа-группа {media_group_text}\n\n'
            else:
                user_id = ticket.get('user_id')
                user_info = f'<b>👤 Пользователь: ({user_id})</b>\nID сообщения: {message_id}\nМедиа-группа {media_group_text}\n\n'
        else:
            if is_manager:
                manager_info = f'<b>🗣️ Менеджер:</b>\nID сообщения: {message_id}\nМедиа-группа {media_group_text}\n\n'
            else:
                user_info = f'<b>👤 Пользователь:</b>\nID сообщения: {message_id}\nМедиа-группа {media_group_text}\n\n'

        if is_manager:
            message_text += manager_info
        else:
            message_text += user_info

        if text:
            if msg_caption:
                message_text += '<i>В данном сообщении присутствует медиафайл!</i>\n\n'
            message_text += text + '\n____________________________________\n\n'
        else:
            message_text += '<i>В данном сообщении присутствует медиафайл!</i> \n'
            message_text += '____________________________________\n\n'

    return message_text


async def get_media_messages(page: int, ticket: dict) -> list[Message]:
    content = ticket.get('content')
    content = content if content else []

    upper = page * BATCH if len(content) > page * BATCH else len(content)
    lower = upper - BATCH if upper - BATCH >= 0 else 0

    messages = []
    for i in range(lower, upper):
        msg_info = content[i]
        message_id = msg_info.get('message_id')
        media_group_id = msg_info.get('media_group_id')
        media_group_text = media_group_id if media_group_id else 'Отсутствует'

        path = f'{cf.project["storage"]}/{ticket.get("ticket_id")}/media_info.txt'
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-16') as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith(f'{message_id} {media_group_id}'):
                        message = Message(**msg_info)
                        caption = message.html_text
                        if caption:
                            caption = f'<b>ID сообщения:</b> {message_id}\n<b>Медиа-группа:</b> {media_group_text}\n\n' + caption
                        else:
                            caption = f'<b>ID сообщения:</b> {message_id}\n<b>Медиа-группа:</b> {media_group_text}\n\n'

                        msg_info = message.model_dump()
                        msg_info['caption'] = caption
                        messages.append(Message(**msg_info))

    return messages


async def make_up_tickets_info_page(page: int, tickets: list[dict], is_extended: bool = False):
    upper = page * BATCH if len(tickets) > page * BATCH else len(tickets)
    lower = upper - BATCH if upper - BATCH >= 0 else 0

    tickets_info = f'<b>Беседы |{upper}/{len(tickets)}|</b>\n\n'
    for i in range(lower, upper):
        ticket = tickets[i]
        ticket_id = ticket.get('ticket_id')
        opened = str(ticket.get('open_date')).split('.')[0]
        closed = str(ticket.get('close_date')).replace('None', '|еще открыт!|').split('.')[0]
        comment = ticket.get('comment', 'Отсутствует')
        name, title, description = ticket.get('user_name'), ticket.get('title'), ticket.get('description')
        tg_name = ticket.get('tg_name')

        tickets_info += f'<b>Беседа:</b> {ticket_id}\n'
        tickets_info += f'<b>Создан:</b> {opened} по МСК\n'
        tickets_info += f'<b>Закрыт:</b> {closed} по МСК\n'
        tickets_info += f'<b>Имя пользователя:</b> {name}\n'
        tickets_info += f'<b>Имя ТГ:</b> {tg_name}\n'
        tickets_info += f'<b>Тема беседы:</b> {title}\n'
        tickets_info += f'<b>Описание беседы:</b> {description}\n'
        if is_extended:
            tickets_info += f'<b>Комментарий:</b> {comment}\n'
        tickets_info += '____________________________________\n\n'

    return tickets_info


async def make_up_user_info(user: dict) -> tuple:
    tg_name, tg_id, status = user.get('user_name'), int(user.get('user_id')), user.get('status')
    mute_time, is_banned = str(user.get('mute_time')), user.get('is_banned')
    url_name = user.get('url_name')
    as_user_tickets = await db.tickets.get_all_by_id(user_id=tg_id, is_manager=False)
    as_manager_tickets = await db.tickets.get_all_by_id(user_id=tg_id, is_manager=True)

    is_manager = False

    status_text = ''
    match status:
        case 'user':
            status_text = 'обычный пользователь'
        case 'manager':
            is_manager = True
            status_text = 'менеджер'
        case 'admin':
            is_manager = True
            status_text = 'администратор'

    text = ''
    text += f'<b>ТГ имя:</b> {tg_name}\n\n'
    text += f'<b>ТГ ID:</b> {tg_id}\n\n'
    text += f'<b>Ссылка:</b> @{url_name}\n\n'
    text += f'<b>Статус:</b> {status_text}\n\n'
    if is_banned:
        text += f'<b>Забанен ли:</b> {"да" if is_banned else "нет"}\n\n'
    else:
        text += f'<b>Запрет на беседы до:</b> {mute_time.split(".")[0] if (mute_time and mute_time != "None") else "нет запретов"}\n\n'
        text += f'<b>Забанен ли:</b> нет\n\n'
    text += f'<b>Кол-во бесед (как пользователь):</b> {0 if not as_user_tickets else len(as_user_tickets)}\n\n'
    text += f'<b>Кол-во бесед (как менеджер):</b> {0 if not as_manager_tickets else len(as_manager_tickets)}'

    return is_manager, text
