"""Роли и статусы. В MongoDB хранятся обычными строками."""


class Role:
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"


STAFF_ROLES = (Role.MANAGER, Role.ADMIN)


class TicketStatus:
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


ACTIVE_STATUSES = (TicketStatus.OPEN, TicketStatus.IN_PROGRESS)


class Sender:
    USER = "user"
    STAFF = "staff"


class CloseReason:
    USER = "user"
    STAFF = "staff"
    AUTO = "auto"
