# app/order_status.py - order status lifecycle helpers
from app.models import OrderStatus

STATUS_ORDER = [
    OrderStatus.PENDING,
    OrderStatus.ACCEPTED,
    OrderStatus.PREPARING,
    OrderStatus.ON_THE_WAY,
    OrderStatus.DELIVERED,
    OrderStatus.CANCELED,
]

ALLOWED_TRANSITIONS = {
    OrderStatus.PENDING: {OrderStatus.ACCEPTED, OrderStatus.CANCELED},
    OrderStatus.ACCEPTED: {OrderStatus.PREPARING, OrderStatus.CANCELED},
    OrderStatus.PREPARING: {OrderStatus.ON_THE_WAY, OrderStatus.CANCELED},
    OrderStatus.ON_THE_WAY: {OrderStatus.DELIVERED, OrderStatus.CANCELED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELED: set(),
}


def is_valid_status(status: str) -> bool:
    return status in STATUS_ORDER


def can_transition(old_status: str, new_status: str) -> bool:
    if new_status == old_status:
        return True
    return new_status in ALLOWED_TRANSITIONS.get(old_status, set())


def status_choices(current_status: str):
    choices = [current_status]
    for status in STATUS_ORDER:
        if status in ALLOWED_TRANSITIONS.get(current_status, set()):
            choices.append(status)
    return choices
