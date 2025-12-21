# app/routes/customer.py - Customer-facing routes (auth and cart simulation)
from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.models import Product, User

customer_bp = Blueprint("customer", __name__)


def _ensure_cart() -> dict:
    """Initialize cart in session if missing."""
    if "cart" not in session:
        session["cart"] = {}
    return session["cart"]


@customer_bp.route("/customer/register", methods=["POST"])
def register_customer():
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not all([name, email, password]):
        return jsonify({"error": "name, email and password are required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email already registered"}), 409

    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        role="customer",
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "customer registered", "user_id": user.id, "role": user.role}), 201


@customer_bp.route("/customer/login", methods=["POST"])
def login_customer():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not all([email, password]):
        return jsonify({"error": "email and password are required"}), 400

    user = User.query.filter_by(email=email, role="customer").first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "invalid credentials"}), 401

    session["user_id"] = user.id
    session["role"] = user.role
    return jsonify({"message": "login successful", "user_id": user.id, "role": user.role})


@customer_bp.route("/cart/add", methods=["POST"])
def add_to_cart():
    data = request.get_json() or {}
    product_id = data.get("product_id")
    quantity = int(data.get("quantity") or 1)

    if not product_id or quantity <= 0:
        return jsonify({"error": "product_id and positive quantity are required"}), 400

    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return jsonify({"error": "product not found or inactive"}), 404

    cart = _ensure_cart()
    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    session.modified = True
    return jsonify({"message": "added", "cart": cart})


@customer_bp.route("/cart/remove", methods=["POST"])
def remove_from_cart():
    data = request.get_json() or {}
    product_id = data.get("product_id")

    if not product_id:
        return jsonify({"error": "product_id is required"}), 400

    cart = _ensure_cart()
    cart.pop(str(product_id), None)
    session.modified = True
    return jsonify({"message": "removed", "cart": cart})


@customer_bp.route("/cart", methods=["GET"])
def get_cart():
    cart = _ensure_cart()
    return jsonify({"cart": cart})
