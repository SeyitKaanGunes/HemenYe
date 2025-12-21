# app/main/__init__.py - main blueprint factory
from flask import Blueprint

main_bp = Blueprint("main", __name__)

from app.main import routes  # noqa: E402,F401
