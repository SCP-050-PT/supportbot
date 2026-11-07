# Project
from bot import bot
import config as cf
from resources import strings as strs
from database import db
from logger import background_logger


async def notify_delete():
    background_logger.info('Notifying admin to delete tickets!')
    admin = await db.users.get_by_id(user_id=cf.admin_id)
    should_notificate = admin.get('should_notificate', True)
    if should_notificate:
        await bot.send_message(
            chat_id=cf.admin_id,
            text=strs.admin_delete_notification
        )
