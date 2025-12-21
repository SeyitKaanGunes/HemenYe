# app/customer/__init__.py - customer blueprint
from flask import Blueprint

customer_bp = Blueprint("customer", __name__)

from app.customer import routes  # noqa: E402,F401
