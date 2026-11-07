# Standard
from datetime import datetime, timezone, timedelta

# Project
from database import db
from logger import background_logger


async def check_mute():
    background_logger.warning('Checking mute time of muted users')
    muted = await db.users.get_all_muted()
    if muted:
        current_time = datetime.now(timezone(timedelta(hours=3)))
        for user in muted:
            mute_time = user.get('mute_time').split('.')[0]
            mute_time = datetime.strptime(mute_time, '%Y-%m-%d %H:%M:%S')
            if mute_time.replace(tzinfo=timezone(timedelta(hours=3))) < current_time:
                await db.users.update(
                    user_id=user.get('user_id'),
                    new_data={
                        'mute_time': None
                    }
                )