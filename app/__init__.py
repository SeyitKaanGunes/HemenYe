# app/__init__.py - application factory
from flask import Flask
from flask_migrate import Migrate
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import OperationalError

from app.config import Config
from app.extensions import db, login_manager


def _ensure_database(uri: str) -> None:
    """For MySQL: create the database if it doesn't exist to avoid connection errors."""
    url = make_url(uri)
    if not url.drivername.startswith("mysql"):
        return
    database_name = url.database
    if not database_name:
        return

    admin_url = url.set(database=None)
    engine = create_engine(admin_url)
    try:
        with engine.connect() as conn:
            conn.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
                    "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
    finally:
        engine.dispose()


def create_app() -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(Config)

    # Ensure DB exists (for MySQL) before binding SQLAlchemy.
    _ensure_database(app.config["SQLALCHEMY_DATABASE_URI"])

    db.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)

    # Import models so metadata is registered before create_all.
    from app import models  # noqa: F401

    # Auto-create tables on startup to prevent "table does not exist" errors in dev.
    with app.app_context():
        try:
            db.create_all()
        except OperationalError as exc:
            # Surface a clear error rather than failing lazily later.
            raise RuntimeError(f"Database connection failed: {exc}") from exc

    from app.models import User  # noqa: F401
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.customer.routes import customer_bp
    from app.restaurant.routes import restaurant_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(restaurant_bp)

    def add_alias(alias: str, target: str):
        view = app.view_functions.get(target)
        if not view:
            return
        for rule in list(app.url_map.iter_rules()):
            if rule.endpoint == target:
                methods = None
                if rule.methods:
                    methods = [m for m in rule.methods if m not in {"HEAD", "OPTIONS"}]
                app.add_url_rule(rule.rule, endpoint=alias, view_func=view, methods=methods)
                break

    aliases = {
        "home": "main.home",
        "customer_login": "auth.customer_login",
        "customer_register": "auth.customer_register",
        "restaurant_login": "auth.restaurant_login",
        "restaurant_register": "auth.restaurant_register",
        "logout": "auth.logout",
        "customer_dashboard": "customer.customer_dashboard",
        "customer_restaurants": "customer.customer_restaurants",
        "customer_cart": "customer.customer_cart",
        "customer_order_summary": "customer.customer_order_summary",
        "customer_orders": "customer.customer_orders",
        "customer_support": "customer.customer_support",
        "customer_addresses": "customer.customer_addresses",
        "customer_favorites": "customer.customer_favorites",
        "restaurant_dashboard": "restaurant.restaurant_dashboard",
        "restaurant_menu": "restaurant.restaurant_menu",
        "restaurant_orders": "restaurant.restaurant_orders",
        "restaurant_reviews": "restaurant.restaurant_reviews",
        "restaurant_support": "restaurant.restaurant_support",
    }
    for alias, target in aliases.items():
        add_alias(alias, target)

    return app
