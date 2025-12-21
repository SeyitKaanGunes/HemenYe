# app/routes/restaurant.py - Restaurant owner auth and public restaurant/menu routes
from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.models import (
    Product,
    ProductOption,
    ProductOptionGroup,
    ProductProductOptionGroup,
    ProductCategory,
    Restaurant,
    RestaurantBranch,
    RestaurantCuisine,
    User,
)

restaurant_bp = Blueprint("restaurant", __name__)


@restaurant_bp.route("/owner/register", methods=["POST"])
def register_owner():
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
        role="restaurant_owner",
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "owner registered", "user_id": user.id, "role": user.role}), 201


@restaurant_bp.route("/owner/login", methods=["POST"])
def login_owner():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not all([email, password]):
        return jsonify({"error": "email and password are required"}), 400

    user = User.query.filter_by(email=email, role="restaurant_owner").first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "invalid credentials"}), 401

    session["user_id"] = user.id
    session["role"] = user.role
    return jsonify({"message": "login successful", "user_id": user.id, "role": user.role})


@restaurant_bp.route("/restaurants", methods=["GET"])
def list_restaurants():
    restaurants = Restaurant.query.filter_by(is_active=1).all()
    response = []
    for r in restaurants:
        branch_count = RestaurantBranch.query.filter_by(restaurant_id=r.id, is_active=1).count()
        cuisine_names = [rc.cuisine.name for rc in RestaurantCuisine.query.filter_by(restaurant_id=r.id).all()]
        response.append(
            {
                "restaurant_id": r.id,
                "name": r.name,
                "phone": r.phone,
                "is_active": bool(r.is_active),
                "branch_count": branch_count,
                "cuisines": cuisine_names,
            }
        )
    return jsonify({"restaurants": response})


@restaurant_bp.route("/restaurants/<int:restaurant_id>/menu", methods=["GET"])
def get_menu(restaurant_id: int):
    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant or not restaurant.is_active:
        return jsonify({"error": "restaurant not found"}), 404

    categories = ProductCategory.query.filter_by(restaurant_id=restaurant_id).all()
    products = Product.query.filter_by(restaurant_id=restaurant_id, is_active=1).all()

    # Preload option groups and options for the restaurant
    option_groups = ProductOptionGroup.query.filter_by(restaurant_id=restaurant_id).all()
    group_options_map = {
        og.option_group_id: [
            {"option_id": opt.option_id, "name": opt.name, "extra_price": float(opt.extra_price), "is_active": bool(opt.is_active)}
            for opt in ProductOption.query.filter_by(option_group_id=og.option_group_id, is_active=1).all()
        ]
        for og in option_groups
    }

    # Map product to option groups through association table
    product_group_map = {}
    links = ProductProductOptionGroup.query.join(ProductOptionGroup).filter(
        ProductOptionGroup.restaurant_id == restaurant_id
    )
    for link in links:
        product_group_map.setdefault(link.product_id, []).append(link.option_group_id)

    # Build category -> products structure
    categories_payload = []
    for cat in categories:
        categories_payload.append(
            {
                "category_id": cat.category_id,
                "name": cat.name,
                "parent_category_id": cat.parent_category_id,
                "products": [
                    {
                        "product_id": p.product_id,
                        "name": p.name,
                        "description": p.description,
                        "base_price": float(p.base_price),
                        "option_groups": [
                            {
                                "option_group_id": og_id,
                                "options": group_options_map.get(og_id, []),
                            }
                            for og_id in product_group_map.get(p.product_id, [])
                        ],
                    }
                    for p in products
                    if p.category_id == cat.category_id
                ],
            }
        )

    return jsonify(
        {
            "restaurant": {"restaurant_id": restaurant.id, "name": restaurant.name},
            "categories": categories_payload,
        }
    )
