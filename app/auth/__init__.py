# app/auth/__init__.py - auth blueprint
from flask import Blueprint

auth_bp = Blueprint("auth", __name__)

from app.auth import routes  # noqa: E402,F401
