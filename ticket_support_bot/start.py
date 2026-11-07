# Third-party
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Standard
import asyncio


# Project
from bot import bot, dispatcher
from handlers import all_routers
from handlers import background as back
from database import generate_start_data

dispatcher.include_routers(*all_routers)


async def start_bot():
    await bot.delete_webhook(drop_pending_updates=True)

    await dispatcher.start_polling(
        bot,
        allowed_updates=[
            'message', 'callback_query'
        ]  # Add needed router updates
    )


async def run_app():
    await asyncio.gather(
        generate_start_data(),
        start_bot(),
    )


if __name__ == '__main__':
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_app)
    scheduler.add_job(
        back.check_mute,
        trigger='interval',
        minutes=1
    )
    scheduler.add_job(
        back.release_check,
        trigger='interval',
        minutes=35
    )
    scheduler.add_job(
        back.close_check,
        trigger='interval',
        hours=1
    )
    scheduler.add_job(
        back.notify_delete,
        trigger=CronTrigger(day=1),
    )
    scheduler.start()
    asyncio.get_event_loop().run_forever()
