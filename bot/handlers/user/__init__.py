from aiogram import Router

from bot.db.constants import Role
from bot.filters import RoleFilter
from bot.handlers.user import tickets

router = Router(name="user")
router.message.filter(RoleFilter(Role.USER))
router.callback_query.filter(RoleFilter(Role.USER))
router.include_router(tickets.router)
