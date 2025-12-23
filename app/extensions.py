# app/extensions.py - shared extensions (db, login_manager)
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.customer_login"
login_manager.blueprint_login_views = {
    "restaurant": "auth.restaurant_login",
    "admin": "admin.admin_login",
}
login_manager.login_message_category = "warning"
