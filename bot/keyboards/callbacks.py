"""Данные inline-кнопок (CallbackData). Значения не должны содержать двоеточие."""
from aiogram.filters.callback_data import CallbackData


class TicketCb(CallbackData, prefix="t"):
    action: str  # view | accept | history
    ticket_id: int


class FaqCb(CallbackData, prefix="f"):
    action: str  # list | show | del
    faq_id: str = ""


class UserCb(CallbackData, prefix="u"):
    action: str  # tickets | promote | demote | mute | unmute | ban | unban
    user_id: int
    value: int = 0


class AdminCb(CallbackData, prefix="a"):
    action: str
    value: str = ""


CHECK_SUB = "check_sub"
