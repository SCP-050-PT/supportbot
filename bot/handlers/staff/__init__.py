from aiogram import Router

from bot.db.constants import STAFF_ROLES
from bot.filters import RoleFilter
from bot.handlers.staff import tickets, users

router = Router(name="staff")
router.message.filter(RoleFilter(*STAFF_ROLES))
router.callback_query.filter(RoleFilter(*STAFF_ROLES))
router.include_routers(users.router, tickets.router)
