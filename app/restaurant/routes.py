# app/restaurant/routes.py - restaurant owner views
from flask import render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (
    Restaurant,
    Product,
    ProductCategory,
    Order,
    Review,
    UserRole,
    User,
    OrderItem,
    ReviewReply,
    RestaurantBranch,
    OrderStatusHistory,
    ProductPriceHistory,
)
from app.restaurant import restaurant_bp
from app.order_status import can_transition, status_choices, is_valid_status
from app.pagination import paginate


def owner_required():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.restaurant_login"))
    if current_user.role != UserRole.RESTAURANT_OWNER:
        abort(403)
    return None


def _current_restaurant():
    return Restaurant.query.filter_by(owner_id=current_user.id).first()


@restaurant_bp.route("/restaurant/dashboard", endpoint="restaurant_dashboard")
@login_required
def dashboard():
    gate = owner_required()
    if gate:
        return gate
    restaurant = _current_restaurant()
    stats = {"total_orders": 0, "today_orders": 0, "avg_rating": "-"}
    return render_template("restaurant/dashboard.html", restaurant=restaurant, stats=stats)


@restaurant_bp.route("/restaurant/menu", endpoint="restaurant_menu")
@login_required
def menu():
    gate = owner_required()
    if gate:
        return gate
    restaurant = _current_restaurant()
    products = Product.query.filter_by(restaurant_id=restaurant.id).all() if restaurant else []
    return render_template("restaurant/menu.html", products=products)


@restaurant_bp.route("/restaurant/products/new", methods=["GET", "POST"])
@login_required
def product_new():
    gate = owner_required()
    if gate:
        return gate
    restaurant = _current_restaurant()
    categories = ProductCategory.query.filter_by(restaurant_id=restaurant.id).all() if restaurant else []
    if request.method == "POST":
        if not restaurant:
            flash("Restaurant not found for owner.", "danger")
            return redirect(url_for("restaurant_dashboard"))
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        category_id = request.form.get("category_id")
        price_raw = request.form.get("price")
        try:
            price = float(price_raw)
        except (TypeError, ValueError):
            price = None
        if not name or not category_id or price is None or price < 0:
            flash("Name, category, and valid price are required.", "danger")
            return render_template(
                "restaurant/product_form.html",
                product=None,
                categories=categories,
                option_groups=[],
                selected_option_groups=[],
                form_action=url_for("restaurant.product_new"),
            )
        valid_category = ProductCategory.query.filter_by(id=category_id, restaurant_id=restaurant.id).first()
        if not valid_category:
            flash("Invalid category.", "danger")
            return render_template(
                "restaurant/product_form.html",
                product=None,
                categories=categories,
                option_groups=[],
                selected_option_groups=[],
                form_action=url_for("restaurant.product_new"),
            )
        p = Product(
            restaurant_id=restaurant.id,
            category_id=category_id,
            name=name,
            description=description,
            price=price,
            is_active=bool(request.form.get("is_active")),
        )
        db.session.add(p)
        db.session.commit()
        flash("Product created.", "success")
        return redirect(url_for("restaurant_menu"))
    return render_template(
        "restaurant/product_form.html",
        product=None,
        categories=categories,
        option_groups=[],
        selected_option_groups=[],
        form_action=url_for("restaurant.product_new"),
    )


@restaurant_bp.route("/restaurant/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def product_edit(product_id):
    gate = owner_required()
    if gate:
        return gate
    product = Product.query.get_or_404(product_id)
    restaurant = _current_restaurant()
    if not restaurant or product.restaurant_id != restaurant.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("restaurant_menu"))
    categories = ProductCategory.query.filter_by(restaurant_id=restaurant.id).all()
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        category_id = request.form.get("category_id")
        price_raw = request.form.get("price")
        try:
            price = float(price_raw)
        except (TypeError, ValueError):
            price = None
        if not name or not category_id or price is None or price < 0:
            flash("Name, category, and valid price are required.", "danger")
            return render_template(
                "restaurant/product_form.html",
                product=product,
                categories=categories,
                option_groups=[],
                selected_option_groups=[],
                form_action=url_for("restaurant.product_edit", product_id=product.id),
            )
        valid_category = ProductCategory.query.filter_by(id=category_id, restaurant_id=restaurant.id).first()
        if not valid_category:
            flash("Invalid category.", "danger")
            return render_template(
                "restaurant/product_form.html",
                product=product,
                categories=categories,
                option_groups=[],
                selected_option_groups=[],
                form_action=url_for("restaurant.product_edit", product_id=product.id),
            )
        old_price = product.price
        product.name = name
        product.description = description
        product.category_id = category_id
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
        return redirect(url_for("restaurant_menu"))
    return render_template(
        "restaurant/product_form.html",
        product=product,
        categories=categories,
        option_groups=[],
        selected_option_groups=[],
        form_action=url_for("restaurant.product_edit", product_id=product.id),
    )


@restaurant_bp.route("/restaurant/products/<int:product_id>/delete", methods=["POST"])
@login_required
def product_delete(product_id):
    gate = owner_required()
    if gate:
        return gate
    product = Product.query.get_or_404(product_id)
    restaurant = _current_restaurant()
    if not restaurant or product.restaurant_id != restaurant.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("restaurant_menu"))
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted.", "info")
    return redirect(url_for("restaurant_menu"))


@restaurant_bp.route("/restaurant/orders", endpoint="restaurant_orders")
@login_required
def orders():
    gate = owner_required()
    if gate:
        return gate
    restaurant = _current_restaurant()
    status_filter = request.args.get("status")
    search_query = (request.args.get("q") or "").strip()
    if restaurant:
        query = (
            Order.query.join(RestaurantBranch, Order.branch_id == RestaurantBranch.id)
            .filter(RestaurantBranch.restaurant_id == restaurant.id)
        )
    else:
        query = Order.query.filter(False)
    if status_filter and is_valid_status(status_filter):
        query = query.filter(Order.status == status_filter)
    else:
        status_filter = ""
    if search_query:
        if search_query.isdigit():
            query = query.filter(Order.id == int(search_query))
        else:
            query = query.join(User, Order.user_id == User.id).filter(User.name.ilike(f"%{search_query}%"))
    page = request.args.get("page", 1, type=int)
    per_page = 10
    orders_list, page, pages, total = paginate(query.order_by(Order.id.desc()), page, per_page)
    for order in orders_list:
        order.status_options = status_choices(order.status)
    return render_template("restaurant/orders.html", orders=orders_list, status_filter=status_filter, search_query=search_query, page=page, pages=pages)


@restaurant_bp.route("/restaurant/orders/<int:order_id>", methods=["GET", "POST"])
@login_required
def order_detail(order_id):
    gate = owner_required()
    if gate:
        return gate
    restaurant = _current_restaurant()
    order = (
        Order.query.join(RestaurantBranch, Order.branch_id == RestaurantBranch.id)
        .filter(Order.id == order_id, RestaurantBranch.restaurant_id == (restaurant.id if restaurant else None))
        .first_or_404()
    )
    if request.method == "POST":
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
                    order_id=order.id, old_status=old_status, new_status=new_status, changed_by_user_id=current_user.id
                )
            )
            db.session.commit()
            flash("Order status updated.", "success")
    status_history = (
        OrderStatusHistory.query.filter_by(order_id=order.id).order_by(OrderStatusHistory.changed_at.desc()).all()
    )
    return render_template("restaurant/order_detail.html", order=order, status_history=status_history, status_options=status_choices(order.status))


@restaurant_bp.route("/restaurant/orders/<int:order_id>/status", methods=["POST"])
@login_required
def order_status_update(order_id):
    gate = owner_required()
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
            OrderStatusHistory(order_id=order.id, old_status=old_status, new_status=new_status, changed_by_user_id=current_user.id)
        )
        db.session.commit()
        flash("Order status updated.", "success")
    return redirect(url_for("restaurant_orders"))


@restaurant_bp.route("/restaurant/reviews", methods=["GET", "POST"], endpoint="restaurant_reviews")
@login_required
def reviews():
    gate = owner_required()
    if gate:
        return gate
    restaurant = _current_restaurant()
    reviews_list = Review.query.filter_by(restaurant_id=restaurant.id).order_by(Review.created_at.desc()).all() if restaurant else []
    return render_template("restaurant/reviews.html", reviews=reviews_list)


@restaurant_bp.route("/restaurant/reviews/<int:review_id>/reply", methods=["POST"])
@login_required
def review_reply(review_id):
    gate = owner_required()
    if gate:
        return gate
    reply_text = request.form.get("reply")
    if reply_text:
        reply = ReviewReply(review_id=review_id, owner_id=current_user.id, message=reply_text)
        db.session.add(reply)
        db.session.commit()
        flash("Cevap gönderildi.", "success")
    return redirect(url_for("restaurant_reviews"))


@restaurant_bp.route("/restaurant/support", endpoint="restaurant_support")
@login_required
def support():
    gate = owner_required()
    if gate:
        return gate
    tickets = []
    messages = []
    return render_template("restaurant/support_tickets.html", tickets=tickets, messages=messages)


@restaurant_bp.route("/restaurant/support/send", methods=["POST"])
@login_required
def support_send():
    gate = owner_required()
    if gate:
        return gate
    flash("Mesaj gönderildi (örnek).", "info")
    return redirect(url_for("restaurant_support"))
