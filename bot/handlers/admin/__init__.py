from aiogram import Router

from bot.db.constants import Role
from bot.filters import RoleFilter
from bot.handlers.admin import broadcast, faq, panel

router = Router(name="admin")
router.message.filter(RoleFilter(Role.ADMIN))
router.callback_query.filter(RoleFilter(Role.ADMIN))
router.include_routers(panel.router, faq.router, broadcast.router)
