# app/restaurant/routes.py - restaurant owner views
from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (
    Restaurant,
    Product,
    ProductCategory,
    Order,
    Review,
    UserRole,
    OrderItem,
    ReviewReply,
    RestaurantBranch,
    OrderStatusHistory,
    ProductPriceHistory,
)
from app.restaurant import restaurant_bp


def owner_required():
    if not current_user.is_authenticated or current_user.role != UserRole.RESTAURANT_OWNER:
        return redirect(url_for("auth.restaurant_login"))
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
        p = Product(
            restaurant_id=restaurant.id,
            category_id=request.form.get("category_id"),
            name=request.form.get("name"),
            description=request.form.get("description"),
            price=request.form.get("price") or 0,
            is_active=bool(request.form.get("is_active")),
        )
        db.session.add(p)
        db.session.commit()
        flash("Ürün eklendi.", "success")
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
    categories = ProductCategory.query.filter_by(restaurant_id=product.restaurant_id).all()
    if request.method == "POST":
        old_price = product.price
        product.name = request.form.get("name")
        product.description = request.form.get("description")
        product.category_id = request.form.get("category_id")
        product.price = request.form.get("price") or 0
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
        flash("Ürün güncellendi.", "success")
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
    db.session.delete(product)
    db.session.commit()
    flash("Ürün silindi.", "info")
    return redirect(url_for("restaurant_menu"))


@restaurant_bp.route("/restaurant/orders", endpoint="restaurant_orders")
@login_required
def orders():
    gate = owner_required()
    if gate:
        return gate
    restaurant = _current_restaurant()
    orders_list = (
        Order.query.join(RestaurantBranch, Order.branch_id == RestaurantBranch.id)
        .filter(RestaurantBranch.restaurant_id == restaurant.id)
        .order_by(Order.id.desc())
        .all()
        if restaurant
        else []
    )
    return render_template("restaurant/orders.html", orders=orders_list)


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
        if new_status != old_status:
            order.status = new_status
            db.session.add(
                OrderStatusHistory(
                    order_id=order.id, old_status=old_status, new_status=new_status, changed_by_user_id=current_user.id
                )
            )
            db.session.commit()
            flash("Sipariş durumu güncellendi.", "success")
    status_history = (
        OrderStatusHistory.query.filter_by(order_id=order.id).order_by(OrderStatusHistory.changed_at.desc()).all()
    )
    return render_template("restaurant/order_detail.html", order=order, status_history=status_history)


@restaurant_bp.route("/restaurant/orders/<int:order_id>/status", methods=["POST"])
@login_required
def order_status_update(order_id):
    gate = owner_required()
    if gate:
        return gate
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status", order.status)
    old_status = order.status
    if new_status != old_status:
        order.status = new_status
        db.session.add(
            OrderStatusHistory(order_id=order.id, old_status=old_status, new_status=new_status, changed_by_user_id=current_user.id)
        )
        db.session.commit()
        flash("Durum güncellendi.", "success")
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
