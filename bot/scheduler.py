"""Планировщик фоновых задач (APScheduler)."""
from __future__ import annotations

from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.db import Database
from bot.services.jobs import cleanup_old, close_inactive, release_stale
from bot.services.tickets import TicketService


def setup_scheduler(db: Database, ts: TicketService, tz: ZoneInfo) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(
        timezone=tz,
        job_defaults={"max_instances": 1, "coalesce": True, "misfire_grace_time": 60},
    )
    scheduler.add_job(release_stale, "interval", minutes=5, args=(db, ts), id="release_stale")
    scheduler.add_job(close_inactive, "interval", minutes=15, args=(db, ts), id="close_inactive")
    scheduler.add_job(cleanup_old, "cron", hour=4, minute=0, args=(db,), id="cleanup_old")
    return scheduler
