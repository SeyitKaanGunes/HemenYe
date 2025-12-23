# app/admin/routes.py - admin panel routes
from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_user, current_user
from werkzeug.security import check_password_hash
from sqlalchemy import or_

from app.admin import admin_bp
from app.extensions import db
from app.models import (
    User,
    UserRole,
    Restaurant,
    RestaurantBranch,
    Product,
    ProductCategory,
    Order,
    OrderStatusHistory,
    ProductPriceHistory,
)
from app.order_status import can_transition, status_choices, is_valid_status
from app.pagination import paginate


def admin_required():
    if not current_user.is_authenticated:
        return redirect(url_for("admin.admin_login"))
    if current_user.role != UserRole.ADMIN:
        abort(403)
    return None


@admin_bp.route("/admin/login", methods=["GET", "POST"], endpoint="admin_login")
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        user = User.query.filter_by(email=email, role=UserRole.ADMIN).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=bool(request.form.get("remember")))
            flash("Admin login successful.", "success")
            return redirect(url_for("admin.admin_dashboard"))
        flash("Invalid admin credentials.", "danger")
    return render_template("admin/login.html")


@admin_bp.route("/admin", endpoint="admin_dashboard")
def dashboard():
    gate = admin_required()
    if gate:
        return gate
    stats = {
        "users": User.query.count(),
        "restaurants": Restaurant.query.count(),
        "orders": Order.query.count(),
    }
    return render_template("admin/dashboard.html", stats=stats)


@admin_bp.route("/admin/restaurants", endpoint="admin_restaurants")
def restaurants():
    gate = admin_required()
    if gate:
        return gate
    restaurants_list = Restaurant.query.order_by(Restaurant.id.desc()).all()
    return render_template("admin/restaurants.html", restaurants=restaurants_list)


@admin_bp.route("/admin/restaurants/<int:restaurant_id>/toggle", methods=["POST"])
def restaurant_toggle(restaurant_id):
    gate = admin_required()
    if gate:
        return gate
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    restaurant.is_active = not restaurant.is_active
    db.session.commit()
    flash("Restaurant status updated.", "info")
    return redirect(url_for("admin.admin_restaurants"))


@admin_bp.route("/admin/orders", endpoint="admin_orders")
def orders():
    gate = admin_required()
    if gate:
        return gate
    status_filter = request.args.get("status")
    search_query = (request.args.get("q") or "").strip()
    query = Order.query
    if status_filter and is_valid_status(status_filter):
        query = query.filter(Order.status == status_filter)
    else:
        status_filter = ""
    if search_query:
        if search_query.isdigit():
            query = query.filter(Order.id == int(search_query))
        else:
            query = (
                query.join(User, Order.user_id == User.id)
                .join(RestaurantBranch, Order.branch_id == RestaurantBranch.id)
                .join(Restaurant, RestaurantBranch.restaurant_id == Restaurant.id)
                .filter(or_(User.name.ilike(f"%{search_query}%"), Restaurant.name.ilike(f"%{search_query}%")))
            )
    page = request.args.get("page", 1, type=int)
    per_page = 12
    orders_list, page, pages, total = paginate(query.order_by(Order.id.desc()), page, per_page)
    for order in orders_list:
        order.status_options = status_choices(order.status)
    return render_template("admin/orders.html", orders=orders_list, status_filter=status_filter, search_query=search_query, page=page, pages=pages)


@admin_bp.route("/admin/orders/<int:order_id>", endpoint="admin_order_detail")
def order_detail(order_id):
    gate = admin_required()
    if gate:
        return gate
    order = Order.query.get_or_404(order_id)
    status_history = (
        OrderStatusHistory.query.filter_by(order_id=order.id)
        .order_by(OrderStatusHistory.changed_at.desc())
        .all()
    )
    return render_template("admin/order_detail.html", order=order, status_history=status_history, status_options=status_choices(order.status))


@admin_bp.route("/admin/orders/<int:order_id>/status", methods=["POST"])
def order_status_update(order_id):
    gate = admin_required()
    if gate:
        return gate
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status", order.status)
    old_status = order.status
    if not is_valid_status(new_status):
        flash("Invalid status.", "danger")
    elif not can_transition(old_status, new_status):
        flash("Invalid status transition.", "danger")
    elif new_status != old_status:
        order.status = new_status
        db.session.add(
            OrderStatusHistory(
                order_id=order.id,
                old_status=old_status,
                new_status=new_status,
                changed_by_user_id=current_user.id,
            )
        )
        db.session.commit()
        flash("Order status updated.", "success")
    return redirect(url_for("admin.admin_orders"))


def _load_restaurant_context(selected_restaurant_id):
    restaurants = Restaurant.query.order_by(Restaurant.name).all()
    categories = []
    if selected_restaurant_id:
        categories = ProductCategory.query.filter_by(restaurant_id=selected_restaurant_id).order_by(ProductCategory.name).all()
    return restaurants, categories


@admin_bp.route("/admin/products", endpoint="admin_products")
def products():
    gate = admin_required()
    if gate:
        return gate
    restaurant_id = request.args.get("restaurant_id", type=int)
    query = Product.query
    if restaurant_id:
        query = query.filter_by(restaurant_id=restaurant_id)
    products_list = query.order_by(Product.id.desc()).all()
    restaurants, _ = _load_restaurant_context(restaurant_id)
    return render_template(
        "admin/products.html",
        products=products_list,
        restaurants=restaurants,
        selected_restaurant_id=restaurant_id,
    )


@admin_bp.route("/admin/products/new", methods=["GET", "POST"])
def product_new():
    gate = admin_required()
    if gate:
        return gate
    selected_restaurant_id = request.args.get("restaurant_id", type=int)
    if request.method == "POST":
        restaurant_id = request.form.get("restaurant_id", type=int)
        category_id = request.form.get("category_id", type=int)
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        price_raw = request.form.get("price")
        try:
            price = float(price_raw)
        except (TypeError, ValueError):
            price = None
        if not restaurant_id or not category_id or not name or price is None or price < 0:
            flash("Restaurant, category, name, and valid price are required.", "danger")
        else:
            restaurant = Restaurant.query.get(restaurant_id)
            category = ProductCategory.query.filter_by(id=category_id, restaurant_id=restaurant_id).first()
            if not restaurant or not category:
                flash("Invalid restaurant or category.", "danger")
            else:
                product = Product(
                    restaurant_id=restaurant_id,
                    category_id=category_id,
                    name=name,
                    description=description,
                    price=price,
                    is_active=bool(request.form.get("is_active")),
                )
                db.session.add(product)
                db.session.commit()
                flash("Product created.", "success")
                return redirect(url_for("admin.admin_products", restaurant_id=restaurant_id))
        selected_restaurant_id = restaurant_id or selected_restaurant_id
    restaurants, categories = _load_restaurant_context(selected_restaurant_id)
    return render_template(
        "restaurant/product_form.html",
        product=None,
        categories=categories,
        option_groups=[],
        selected_option_groups=[],
        form_action=url_for("admin.product_new", restaurant_id=selected_restaurant_id) if selected_restaurant_id else url_for("admin.product_new"),
        show_restaurant_select=True,
        restaurants=restaurants,
        selected_restaurant_id=selected_restaurant_id,
    )


@admin_bp.route("/admin/products/<int:product_id>/edit", methods=["GET", "POST"])
def product_edit(product_id):
    gate = admin_required()
    if gate:
        return gate
    product = Product.query.get_or_404(product_id)
    selected_restaurant_id = product.restaurant_id
    if request.method == "POST":
        restaurant_id = request.form.get("restaurant_id", type=int)
        category_id = request.form.get("category_id", type=int)
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        price_raw = request.form.get("price")
        try:
            price = float(price_raw)
        except (TypeError, ValueError):
            price = None
        if not restaurant_id or not category_id or not name or price is None or price < 0:
            flash("Restaurant, category, name, and valid price are required.", "danger")
        else:
            restaurant = Restaurant.query.get(restaurant_id)
            category = ProductCategory.query.filter_by(id=category_id, restaurant_id=restaurant_id).first()
            if not restaurant or not category:
                flash("Invalid restaurant or category.", "danger")
            else:
                old_price = product.price
                product.restaurant_id = restaurant_id
                product.category_id = category_id
                product.name = name
                product.description = description
                product.price = price
                product.is_active = bool(request.form.get("is_active"))
                db.session.flush()
                if old_price != product.price:
                    db.session.add(
                        ProductPriceHistory(
                            product_id=product.id,
                            old_price=old_price,
                            new_price=product.price,
                            changed_by_user_id=current_user.id,
                        )
                    )
                db.session.commit()
                flash("Product updated.", "success")
                return redirect(url_for("admin.admin_products", restaurant_id=restaurant_id))
        selected_restaurant_id = restaurant_id or selected_restaurant_id
    restaurants, categories = _load_restaurant_context(selected_restaurant_id)
    return render_template(
        "restaurant/product_form.html",
        product=product,
        categories=categories,
        option_groups=[],
        selected_option_groups=[],
        form_action=url_for("admin.product_edit", product_id=product.id),
        show_restaurant_select=True,
        restaurants=restaurants,
        selected_restaurant_id=selected_restaurant_id,
    )


@admin_bp.route("/admin/products/<int:product_id>/delete", methods=["POST"])
def product_delete(product_id):
    gate = admin_required()
    if gate:
        return gate
    product = Product.query.get_or_404(product_id)
    restaurant_id = product.restaurant_id
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted.", "info")
    return redirect(url_for("admin.admin_products", restaurant_id=restaurant_id))
