# app/restaurant/__init__.py - restaurant owner blueprint
from flask import Blueprint

restaurant_bp = Blueprint("restaurant", __name__)

from app.restaurant import routes  # noqa: E402,F401
