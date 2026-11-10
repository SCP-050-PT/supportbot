"""Все тексты бота в одном месте (HTML-разметка)."""
from __future__ import annotations

import html
from typing import Any
from zoneinfo import ZoneInfo

from bot.db.constants import Role, Sender, TicketStatus
from bot.utils import fmt_dt


def esc(value: Any) -> str:
    """Экранирует пользовательский текст для parse_mode=HTML."""
    return html.escape(str(value if value is not None else ""), quote=False)


STATUS_LABELS = {
    TicketStatus.OPEN: "🟡 Открыто",
    TicketStatus.IN_PROGRESS: "🟢 В работе",
    TicketStatus.CLOSED: "⚪️ Закрыто",
}
ROLE_LABELS = {
    Role.USER: "👤 Пользователь",
    Role.MANAGER: "🧑‍💼 Менеджер",
    Role.ADMIN: "👑 Администратор",
}
MEDIA_LABELS = {
    "photo": "📷 Фото",
    "video": "🎬 Видео",
    "document": "📎 Файл",
    "audio": "🎵 Аудио",
    "voice": "🎤 Голосовое",
    "video_note": "⏺ Видеокружок",
    "sticker": "🔖 Стикер",
    "animation": "🎞 GIF",
}
CLOSE_REASONS = {
    "user": "пользователем",
    "staff": "менеджером",
    "auto": "автоматически (нет активности)",
}
TIMER_NAMES = {
    "release_hours": "Возврат в очередь, если менеджер молчит (часы)",
    "close_hours": "Автозакрытие без активности (часы)",
    "retention_days": "Хранение закрытых обращений (дни)",
}

# ───────────── Общие ─────────────
UNKNOWN_ERROR = "😔 Что-то пошло не так. Попробуйте ещё раз чуть позже."
CANCELLED = "🚫 Действие отменено."
NOTHING_TO_CANCEL = "ℹ️ Отменять нечего."
USER_ID = "🆔 Ваш Telegram ID: <code>{id}</code>"
BANNED = "⛔️ Доступ к боту ограничен."
MUTED = "🔇 Вы временно не можете писать в поддержку (до {until})."
SUBSCRIBE_REQUIRED = (
    "📢 Чтобы пользоваться ботом, подпишитесь на канал <b>{title}</b>, "
    "затем нажмите «✅ Я подписался»."
)
SUBSCRIBE_NOT_YET = "Подписка пока не найдена 🙁"
SUBSCRIBE_OK = "Спасибо за подписку! 🎉"

# ───────────── Пользователь ─────────────
ASK_TITLE = "📝 Коротко опишите тему обращения (до 100 символов):"
TITLE_INVALID = "⚠️ Тема — это текст от 1 до 100 символов. Попробуйте ещё раз:"
ASK_DESCRIPTION = "✍️ Теперь подробно опишите проблему (до 2000 символов):"
DESCRIPTION_INVALID = "⚠️ Описание — это текст до 2000 символов. Попробуйте ещё раз:"
ALREADY_HAS_TICKET = (
    "ℹ️ У вас уже есть активное обращение №{id}. "
    "Пишите сообщения прямо сюда — менеджер их увидит."
)
TICKET_CREATED = (
    "✅ Обращение №{id} создано!\n\n"
    "Как только менеджер его примет, вы получите уведомление. "
    "Дополнительные сообщения и файлы можно отправлять прямо сюда."
)
NO_ACTIVE_TICKET = "ℹ️ У вас нет активного обращения. Нажмите «📝 Создать обращение»."
TICKET_CLOSED_BY_USER = "✅ Обращение №{id} закрыто. Спасибо, что обратились!"
MESSAGE_QUEUED = "📨 Добавлено к обращению №{id}. Ждём, когда менеджер его примет."
NOT_DELIVERED = "⚠️ Не удалось доставить сообщение, попробуйте позже."
NO_TICKETS = "📂 У вас пока нет обращений."
USE_MENU = "👇 Воспользуйтесь кнопками меню."

USER_TICKET_ACCEPTED = "🟢 Менеджер принял ваше обращение №{id}. Пишите сюда — он на связи."
USER_TICKET_RELEASED = "🟡 Обращение №{id} вернулось в очередь — скоро его подхватит другой менеджер."
USER_TICKET_CLOSED = "⚪️ Обращение №{id} закрыто {reason}. Если вопрос остался — создайте новое."

# ───────────── Сотрудники ─────────────
STAFF_NEW_TICKET = "🆕 <b>Новое обращение</b>"
STAFF_TICKET_RETURNED = "🔁 <b>Обращение вернулось в очередь</b>"
STAFF_ACCEPTED = "✅ Вы приняли обращение №{id}. Все ваши сообщения теперь уходят пользователю."
STAFF_NO_CURRENT = "ℹ️ У вас нет обращения в работе. Откройте «📥 Открытые обращения»."
STAFF_RELEASED = "🔓 Обращение №{id} возвращено в очередь."
STAFF_AUTO_RELEASED = (
    "⏰ Обращение №{id} возвращено в очередь: пользователь слишком долго ждал ответа."
)
STAFF_CLOSED = "🔒 Обращение №{id} закрыто."
STAFF_TICKET_CLOSED_NOTIFY = "⚪️ Обращение №{id} закрыто {reason}."
NO_OPEN_TICKETS = "📭 Открытых обращений нет."
OPEN_TICKETS_HEADER = "📥 <b>Открытые обращения</b> (показаны первые {count}):"
USER_UNAVAILABLE = "⚠️ Пользователь заблокировал бота — сообщение не доставлено."
STAFF_HELLO = "👋 Вы вошли как {role}."

ACCEPT_ERRORS = {
    "busy": "⚠️ У вас уже есть обращение в работе. Закройте или отпустите его.",
    "taken": "⚠️ Это обращение уже взял другой менеджер.",
    "closed": "⚠️ Обращение уже закрыто.",
    "not_found": "⚠️ Обращение не найдено.",
}

ASK_USER_QUERY = "🔎 Отправьте Telegram ID, @username или ссылку t.me/username:"
USER_NOT_FOUND = "😕 Пользователь не найден. Он должен хотя бы раз запустить бота."
STAFF_PROTECTED = "⚠️ Сотрудников ограничивать нельзя. Сначала снимите роль менеджера."
ADMIN_ONLY = "⛔️ Только для администраторов."
ADMIN_ROLE_LOCKED = "⚠️ Администраторы задаются в файле .env (ADMIN_IDS)."
USER_MUTED = "🔇 Пользователь заглушён до {until}."
USER_UNMUTED = "🔊 Ограничение снято."
USER_BANNED = "⛔️ Пользователь заблокирован."
USER_UNBANNED = "✅ Пользователь разблокирован."
YOU_ARE_MANAGER = "🎉 Вам выдана роль менеджера! Нажмите /start, чтобы открыть меню."
YOU_ARE_USER = "ℹ️ Роль менеджера снята. Нажмите /start."
NO_USER_TICKETS = "У пользователя нет обращений."
ROLE_CHANGED = "✅ Роль изменена."
USER_FOUND = "🔎 Пользователь найден:"

# ───────────── Админ ─────────────
ASK_TIMER_VALUE = "⏱ <b>{name}</b>\n\nВведите целое число от {min} до {max} (0 — выключить):"
TIMER_INVALID = "⚠️ Нужно целое число от {min} до {max}. Попробуйте ещё раз:"
TIMER_SAVED = "✅ Сохранено."
START_MESSAGE_CURRENT = "👋 <b>Текущее приветствие:</b>\n\n{text}"
ASK_START_MESSAGE = "✏️ Пришлите новый текст приветствия (форматирование сохранится):"
START_MESSAGE_SAVED = "✅ Приветствие обновлено."
TEXT_REQUIRED = "⚠️ Нужен текст. Попробуйте ещё раз:"

ASK_CHANNEL_ID = (
    "📢 1) Добавьте бота администратором в канал.\n"
    "2) Пришлите сюда @username канала, его ID (-100…) или перешлите любой пост из канала."
)
CHANNEL_NOT_FOUND = "⚠️ Канал не найден или бот не добавлен в него. Попробуйте ещё раз:"
CHANNEL_BOT_NOT_ADMIN = "⚠️ Бот не является администратором канала — без этого проверка подписки не работает."
ASK_CHANNEL_URL = "🔗 Канал приватный. Пришлите ссылку-приглашение (https://t.me/+...):"
CHANNEL_URL_INVALID = "⚠️ Ссылка должна начинаться с https://t.me/. Попробуйте ещё раз:"
CHANNEL_SAVED = "✅ Канал сохранён."
CHANNEL_NOT_CONFIGURED = "⚠️ Сначала укажите канал."
ASK_CHANNEL_BUTTON = "🔤 Пришлите текст кнопки подписки (до 40 символов):"
CHANNEL_BUTTON_INVALID = "⚠️ Текст кнопки — от 1 до 40 символов. Попробуйте ещё раз:"
CHANNEL_BUTTON_SAVED = "✅ Текст кнопки обновлён."

FAQ_EMPTY = "❓ Раздел частых вопросов пока пуст."
FAQ_HEADER = "❓ <b>Частые вопросы</b>\n\nВыберите вопрос:"
FAQ_ADMIN_HEADER = "❓ <b>Управление FAQ</b>\n\nНажмите на вопрос, чтобы удалить его."
FAQ_NOT_FOUND = "⚠️ Вопрос не найден."
ASK_FAQ_QUESTION = "❓ Пришлите текст вопроса (до 200 символов):"
FAQ_QUESTION_INVALID = "⚠️ Вопрос — это текст от 1 до 200 символов. Попробуйте ещё раз:"
ASK_FAQ_ANSWER = "💬 Теперь пришлите ответ (форматирование сохранится):"
FAQ_ADDED = "✅ Вопрос добавлен."
FAQ_DELETED = "🗑 Вопрос удалён."

ASK_BROADCAST = (
    "📣 Пришлите сообщение для рассылки (текст, фото, видео — что угодно). "
    "Оно будет скопировано всем пользователям."
)
BROADCAST_CONFIRM = "👆 Так увидят сообщение пользователи. Получателей: <b>{count}</b>. Отправляем?"
BROADCAST_STARTED = "🚀 Рассылка запущена. Отчёт придёт по завершении."
BROADCAST_CANCELLED = "🚫 Рассылка отменена."
BROADCAST_EXPIRED = "⚠️ Сессия рассылки устарела. Начните заново."
BROADCAST_BUSY = "⚠️ Рассылка уже идёт. Дождитесь отчёта."
MANAGERS_EMPTY = "🧑‍💼 Менеджеров пока нет."
MANAGERS_HINT = (
    "\n\nЧтобы добавить менеджера: «🔎 Найти пользователя» → «⬆️ Сделать менеджером».\n"
    "Нажмите на менеджера ниже, чтобы снять роль."
)


# ───────────── Сборщики текстов ─────────────

def user_link(user_id: int, name: str | None) -> str:
    return f'<a href="tg://user?id={user_id}">{esc(name or user_id)}</a>'


def ticket_card(ticket: dict[str, Any], tz: ZoneInfo, prefix: str = "") -> str:
    lines = []
    if prefix:
        lines.append(prefix)
        lines.append("")
    lines += [
        f"🎫 <b>Обращение №{ticket['_id']}</b>",
        f"Статус: {STATUS_LABELS.get(ticket['status'], ticket['status'])}",
        f"От: {user_link(ticket['user_id'], ticket.get('user_name'))} (<code>{ticket['user_id']}</code>)",
        f"Создано: {fmt_dt(ticket.get('created_at'), tz)}",
        "",
        f"<b>Тема:</b> {esc(ticket.get('title'))}",
        f"<b>Описание:</b>\n{esc(ticket.get('description'))}",
    ]
    return "\n".join(lines)


def _history_line(msg: dict[str, Any], tz: ZoneInfo) -> str:
    who = "👤" if msg.get("sender") == Sender.USER else "🧑‍💼"
    time = fmt_dt(msg.get("created_at"), tz)
    body = esc(msg.get("text") or "")
    media = MEDIA_LABELS.get(msg.get("content_type", ""), "")
    if media:
        body = f"[{media}] {body}".strip()
    return f"{who} <i>{time}</i>\n{body or '—'}"


def ticket_history(ticket: dict[str, Any], messages: list[dict[str, Any]], tz: ZoneInfo) -> str:
    header = f"📜 <b>История обращения №{ticket['_id']}</b>\n<b>Тема:</b> {esc(ticket.get('title'))}\n"
    if not messages:
        return header + "\nСообщений пока нет."
    lines = [_history_line(m, tz) for m in messages]
    # Лимит Telegram — 4096 символов: при переполнении убираем самые старые сообщения
    while lines and len(header) + sum(len(x) + 2 for x in lines) > 4000:
        lines.pop(0)
    return header + "\n" + "\n\n".join(lines)


def user_card(user: dict[str, Any], active_ticket: dict[str, Any] | None, tz: ZoneInfo) -> str:
    username = f"@{esc(user['username'])}" if user.get("username") else "—"
    lines = [
        f"👤 <b>{user_link(user['_id'], user.get('full_name'))}</b>",
        f"ID: <code>{user['_id']}</code>",
        f"Username: {username}",
        f"Роль: {ROLE_LABELS.get(user.get('role', ''), user.get('role'))}",
        f"В боте с: {fmt_dt(user.get('created_at'), tz)}",
    ]
    if user.get("is_banned"):
        lines.append("⛔️ Заблокирован")
    if user.get("muted_until"):
        lines.append(f"🔇 Мут до: {fmt_dt(user['muted_until'], tz)}")
    if active_ticket:
        lines.append(
            f"🎫 Активное обращение: №{active_ticket['_id']} "
            f"({STATUS_LABELS.get(active_ticket['status'])})"
        )
    return "\n".join(lines)


def tickets_list(tickets: list[dict[str, Any]], tz: ZoneInfo, title: str = "📂 <b>Обращения</b>") -> str:
    lines = [title, ""]
    for t in tickets:
        lines.append(
            f"№{t['_id']} · {STATUS_LABELS.get(t['status'], t['status'])} · "
            f"{fmt_dt(t.get('created_at'), tz)}\n<i>{esc(t.get('title'))}</i>"
        )
    return "\n".join(lines)


def admin_panel(stats: dict[str, int], users_count: int) -> str:
    return (
        "⚙️ <b>Админ-панель</b>\n\n"
        f"👥 Пользователей: <b>{users_count}</b>\n"
        f"🟡 Открытых: <b>{stats.get(TicketStatus.OPEN, 0)}</b>\n"
        f"🟢 В работе: <b>{stats.get(TicketStatus.IN_PROGRESS, 0)}</b>\n"
        f"⚪️ Закрытых: <b>{stats.get(TicketStatus.CLOSED, 0)}</b>"
    )


def managers_list(managers: list[dict[str, Any]]) -> str:
    if not managers:
        return MANAGERS_EMPTY + MANAGERS_HINT
    lines = ["🧑‍💼 <b>Менеджеры</b>", ""]
    for m in managers:
        busy = f" — в работе №{m['current_ticket_id']}" if m.get("current_ticket_id") else ""
        lines.append(f"• {user_link(m['_id'], m.get('full_name'))} (<code>{m['_id']}</code>){busy}")
    return "\n".join(lines) + MANAGERS_HINT


def timers(values: dict[str, int]) -> str:
    lines = ["⏱ <b>Таймеры</b>", "", "0 — функция выключена.", ""]
    for key, name in TIMER_NAMES.items():
        lines.append(f"• {name}: <b>{values.get(key, 0)}</b>")
    return "\n".join(lines)


def channel_info(channel: dict[str, Any]) -> str:
    state = "🟢 включена" if channel.get("enabled") else "🔴 выключена"
    title = esc(channel.get("title")) or "не указан"
    url = esc(channel.get("url")) or "—"
    return (
        "📢 <b>Обязательная подписка</b>\n\n"
        f"Проверка: {state}\n"
        f"Канал: {title}\n"
        f"Ссылка: {url}\n"
        f"Текст кнопки: {esc(channel.get('button_text'))}"
    )


def broadcast_report(sent: int, blocked: int, failed: int) -> str:
    return (
        "📣 <b>Рассылка завершена</b>\n\n"
        f"✅ Доставлено: {sent}\n"
        f"🚫 Заблокировали бота: {blocked}\n"
        f"⚠️ Ошибки: {failed}"
    )


def cleanup_done(tickets: int, messages: int) -> str:
    return f"🧹 Очистка выполнена. Удалено обращений: {tickets}, сообщений: {messages}."
