"""Загрузка настроек из .env."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent


class ConfigError(RuntimeError):
    """Ошибка в настройках .env."""


@dataclass(frozen=True, slots=True)
class Config:
    bot_token: str
    admin_ids: frozenset[int]
    mongo_uri: str
    mongo_db: str
    timezone: ZoneInfo
    log_level: str
    logs_dir: Path


def _parse_admin_ids(raw: str) -> frozenset[int]:
    ids: set[int] = set()
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if not part.isdigit():
            raise ConfigError(f"ADMIN_IDS: «{part}» не похоже на Telegram ID")
        ids.add(int(part))
    return frozenset(ids)


def load_config() -> Config:
    load_dotenv(BASE_DIR / ".env")

    token = os.getenv("BOT_TOKEN", "").strip()
    if not token or ":" not in token:
        raise ConfigError("BOT_TOKEN не задан или указан неверно (получите его у @BotFather)")

    admin_ids = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))
    if not admin_ids:
        raise ConfigError("ADMIN_IDS пуст — укажите хотя бы один Telegram ID администратора")

    tz_name = os.getenv("TIMEZONE", "Europe/Moscow").strip()
    try:
        timezone = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ConfigError(
            f"Неизвестный часовой пояс TIMEZONE={tz_name} (на Windows нужен пакет tzdata)"
        ) from exc

    return Config(
        bot_token=token,
        admin_ids=admin_ids,
        mongo_uri=os.getenv("MONGO_URI", "mongodb://localhost:27017").strip(),
        mongo_db=os.getenv("MONGO_DB", "support_bot").strip(),
        timezone=timezone,
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        logs_dir=BASE_DIR / "logs",
    )
