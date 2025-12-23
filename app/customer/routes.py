# app/customer/routes.py - customer-facing routes
from datetime import datetime
from flask import render_template, redirect, url_for, session, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy import func

from app.customer import customer_bp
from app.extensions import db
from app.models import (
    Product,
    Order,
    OrderItem,
    Restaurant,
    ProductCategory,
    UserRole,
    Review,
    RestaurantBranch,
    OrderStatus,
    UserAddress,
    Neighborhood,
    CuisineType,
    RestaurantCuisine,
    City,
    District,
    FavoriteRestaurant,
    FavoriteProduct,
    Coupon,
    UserCoupon,
    DiscountType,
    OrderStatusHistory,
)
from app.pagination import paginate
from app.order_status import is_valid_status


def customer_required():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.customer_login"))
    if current_user.role != UserRole.CUSTOMER:
        abort(403)
    return None


def _get_cart():
    return session.setdefault("cart", {})


def _calculate_cart(cart_data, coupon_info=None, user_id=None):
    subtotal = 0
    for pid, qty in cart_data.items():
        product = Product.query.get(int(pid))
        if product:
            subtotal += float(product.price) * qty

    discount = 0
    coupon_obj = None
    if coupon_info:
        coupon_obj = Coupon.query.get(coupon_info.get("id"))
        if coupon_obj and coupon_obj.is_active:
            now_valid = True
            if coupon_obj.valid_from and coupon_obj.valid_from > datetime.utcnow():
                now_valid = False
            if coupon_obj.valid_to and coupon_obj.valid_to < datetime.utcnow():
                now_valid = False
            if now_valid and subtotal >= float(coupon_obj.min_order_amount or 0):
                # usage check
                if coupon_obj.max_usage_per_user:
                    usage = UserCoupon.query.filter_by(user_id=user_id, coupon_id=coupon_obj.id).first()
                    if usage and usage.usage_count >= coupon_obj.max_usage_per_user:
                        now_valid = False
                if now_valid:
                    if coupon_obj.discount_type == DiscountType.PERCENT:
                        discount = subtotal * float(coupon_obj.value) / 100
                    else:
                        discount = float(coupon_obj.value)
                    discount = min(discount, subtotal)
            else:
                coupon_obj = None
                discount = 0
    total = max(0, subtotal - discount)
    return subtotal, discount, total, coupon_obj


def _get_branch_for_restaurant(restaurant_id: int):
    """Pick an active branch for a restaurant; return None if not available."""
    if not restaurant_id:
        return None
    return RestaurantBranch.query.filter_by(restaurant_id=restaurant_id, is_active=True).first()


def _ensure_user_address(user_id: int, neighborhood_id: int):
    """Fetch or create a simple default address for the user."""
    addr = UserAddress.query.filter_by(user_id=user_id).first()
    if addr:
        return addr
    addr = UserAddress(
        user_id=user_id,
        neighborhood_id=neighborhood_id,
        title="Varsayılan Adres",
        address_line="Adres girilmedi (otomatik)",
        is_default=True,
    )
    db.session.add(addr)
    db.session.flush()
    return addr


@customer_bp.route("/customer/dashboard", endpoint="customer_dashboard")
@login_required
def dashboard():
    gate = customer_required()
    if gate:
        return gate
    recent_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.id.desc()).limit(5).all()
    favorite_restaurants = (
        Restaurant.query.join(FavoriteRestaurant, FavoriteRestaurant.restaurant_id == Restaurant.id)
        .filter(FavoriteRestaurant.user_id == current_user.id)
        .limit(5)
        .all()
    )
    return render_template("customer/dashboard.html", recent_orders=recent_orders, favorite_restaurants=favorite_restaurants)


@customer_bp.route("/customer/restaurants", endpoint="customer_restaurants")
def restaurant_list():
    cuisines = CuisineType.query.order_by(CuisineType.name).all()
    if not cuisines:
        default_names = ["Turk", "Burger", "Pizza", "Doner", "Tatli", "Kahve"]
        for name in default_names:
            db.session.add(CuisineType(name=name))
        db.session.commit()
        cuisines = CuisineType.query.order_by(CuisineType.name).all()

    active_restaurants = Restaurant.query.filter_by(is_active=True).all()
    existing_links = {
        rest_id for (rest_id,) in db.session.query(RestaurantCuisine.restaurant_id).distinct().all()
    }
    missing_restaurants = [r for r in active_restaurants if r.id not in existing_links]
    if cuisines and missing_restaurants:
        for restaurant in missing_restaurants:
            cuisine = cuisines[restaurant.id % len(cuisines)]
            db.session.add(RestaurantCuisine(restaurant_id=restaurant.id, cuisine_id=cuisine.id))
        db.session.commit()

    search_query = (request.args.get("q") or "").strip()
    cuisine_id = request.args.get("cuisine_id", type=int)
    min_rating = request.args.get("min_rating", type=float)
    sort = request.args.get("sort") or "rating"
    if sort not in {"rating", "min_order"}:
        sort = "rating"
    if min_rating and (min_rating < 1 or min_rating > 5):
        min_rating = None
    cuisine_ids = {c.id for c in cuisines}
    if cuisine_id and cuisine_id not in cuisine_ids:
        cuisine_id = None
    page = request.args.get("page", 1, type=int)
    per_page = 9

    rating_subq = (
        db.session.query(Review.restaurant_id.label("restaurant_id"), func.avg(Review.rating).label("avg_rating"))
        .group_by(Review.restaurant_id)
        .subquery()
    )
    min_order_subq = (
        db.session.query(
            RestaurantBranch.restaurant_id.label("restaurant_id"),
            func.min(RestaurantBranch.min_order_amount).label("min_order"),
        )
        .filter(RestaurantBranch.is_active == True)
        .group_by(RestaurantBranch.restaurant_id)
        .subquery()
    )

    query = Restaurant.query.filter_by(is_active=True)
    if search_query:
        query = query.filter(Restaurant.name.ilike(f"%{search_query}%"))
    if cuisine_id:
        query = query.join(RestaurantCuisine, RestaurantCuisine.restaurant_id == Restaurant.id).filter(
            RestaurantCuisine.cuisine_id == cuisine_id
        )

    query = query.outerjoin(rating_subq, rating_subq.c.restaurant_id == Restaurant.id)
    query = query.outerjoin(min_order_subq, min_order_subq.c.restaurant_id == Restaurant.id)

    if min_rating:
        query = query.filter(rating_subq.c.avg_rating >= min_rating)

    if sort == "min_order":
        query = query.order_by(func.coalesce(min_order_subq.c.min_order, 999999).asc(), Restaurant.name.asc())
    else:
        query = query.order_by(func.coalesce(rating_subq.c.avg_rating, 0).desc(), Restaurant.name.asc())

    total = query.count()
    pages = max(1, (total + per_page - 1) // per_page) if total else 1
    if page < 1:
        page = 1
    if page > pages:
        page = pages

    rows = (
        query.with_entities(Restaurant, rating_subq.c.avg_rating, min_order_subq.c.min_order)
        .limit(per_page)
        .offset((page - 1) * per_page)
        .all()
    )

    restaurant_ids = [r.id for r, _, _ in rows]
    cuisine_map = {}
    if restaurant_ids:
        cuisine_rows = (
            db.session.query(RestaurantCuisine.restaurant_id, CuisineType.name)
            .join(CuisineType, RestaurantCuisine.cuisine_id == CuisineType.id)
            .filter(RestaurantCuisine.restaurant_id.in_(restaurant_ids))
            .all()
        )
        for rest_id, cuisine_name in cuisine_rows:
            cuisine_map.setdefault(rest_id, []).append(cuisine_name)

    restaurant_cards = []
    for r, avg_rating, min_order in rows:
        features = []
        if avg_rating is None:
            features.append("Yeni")
        elif avg_rating >= 4.5:
            features.append("Populer")
        if min_order is not None and float(min_order) <= 60:
            features.append("Uygun Min")
        if len(cuisine_map.get(r.id, [])) >= 2:
            features.append("Cesitli")
        restaurant_cards.append(
            {
                "id": r.id,
                "name": r.name,
                "phone": r.phone,
                "cuisines": cuisine_map.get(r.id, []),
                "avg_rating": f"{avg_rating:.1f}" if avg_rating is not None else "-",
                "min_order": f"{float(min_order):.0f}" if min_order is not None else "-",
                "features": features,
            }
        )
    return render_template(
        "customer/restaurant_list.html",
        restaurants=restaurant_cards,
        cuisines=cuisines,
        search_query=search_query,
        selected_cuisine_id=cuisine_id or "",
        selected_min_rating=min_rating or "",
        selected_sort=sort,
        page=page,
        pages=pages,
    )
@customer_bp.route("/customer/restaurants/<int:restaurant_id>")
def restaurant_detail(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    branch = RestaurantBranch.query.filter_by(restaurant_id=restaurant_id, is_active=True).first()
    avg_rating = (
        db.session.query(func.avg(Review.rating)).filter(Review.restaurant_id == restaurant_id).scalar()
    )
    categories = ProductCategory.query.filter_by(restaurant_id=restaurant_id).all()
    # simple grouping
    cat_list = []
    for c in categories:
        cat_list.append(
            {
                "id": c.id,
                "name": c.name,
                "products": Product.query.filter_by(category_id=c.id, is_active=True).all(),
            }
        )
    return render_template(
        "customer/restaurant_detail.html",
        restaurant=restaurant,
        branch=branch,
        avg_rating=f"{avg_rating:.1f}" if avg_rating is not None else "-",
        categories=cat_list,
    )


@customer_bp.route("/customer/cart", endpoint="customer_cart")
@login_required
def cart():
    gate = customer_required()
    if gate:
        return gate
    cart_data = _get_cart()
    items = []
    for pid, qty in cart_data.items():
        product = Product.query.get(int(pid))
        if not product:
            continue
        subtotal = float(product.price) * qty
        items.append({"id": product.id, "name": product.name, "quantity": qty, "unit_price": product.price, "subtotal": subtotal})

    subtotal, discount, total, coupon_obj = _calculate_cart(cart_data, session.get("coupon"), current_user.id)
    totals = {"subtotal": subtotal, "discount": discount, "total": total}
    return render_template("customer/cart.html", cart_items=items, totals=totals, coupon=coupon_obj)


def _redirect_back(default_endpoint: str = "customer_cart"):
    ref = request.referrer or ""
    # Basit güvenlik: yalnızca aynı hosta ait referrer'lara dön.
    if ref and ref.startswith(request.host_url):
        return redirect(ref)
    return redirect(url_for(default_endpoint))


@customer_bp.route("/customer/cart/add", methods=["POST"])
@customer_bp.route("/customer/cart/add/<int:product_id>", methods=["POST"])
@login_required
def cart_add(product_id=None):
    gate = customer_required()
    if gate:
        return gate
    try:
        pid = int(product_id or request.form.get("product_id", 0))
    except (TypeError, ValueError):
        pid = 0
    if not pid:
        flash("Invalid product.", "danger")
        return _redirect_back()
    product = Product.query.get(pid)
    if not product or not product.is_active:
        flash("Product not found or inactive.", "danger")
        return _redirect_back()
    cart_data = _get_cart()
    cart_data[str(pid)] = cart_data.get(str(pid), 0) + 1
    session.modified = True
    flash("Ürün sepete eklendi.", "success")
    return _redirect_back()


@customer_bp.route("/customer/cart/remove", methods=["POST"])
@customer_bp.route("/customer/cart/remove/<int:product_id>", methods=["POST"])
@login_required
def cart_remove(product_id=None):
    gate = customer_required()
    if gate:
        return gate
    try:
        pid = int(product_id or request.form.get("product_id", 0))
    except (TypeError, ValueError):
        pid = 0
    cart_data = _get_cart()
    cart_data.pop(str(pid), None)
    session.modified = True
    flash("Ürün sepetten çıkarıldı.", "info")
    return _redirect_back()


@customer_bp.route("/customer/cart/increase", methods=["POST"])
@customer_bp.route("/customer/cart/increase/<int:product_id>", methods=["POST"])
@login_required
def cart_increase(product_id=None):
    try:
        pid = int(product_id or request.form.get("product_id", 0))
    except (TypeError, ValueError):
        pid = 0
    return cart_add(pid)


@customer_bp.route("/customer/cart/decrease", methods=["POST"])
@customer_bp.route("/customer/cart/decrease/<int:product_id>", methods=["POST"])
@login_required
def cart_decrease(product_id=None):
    gate = customer_required()
    if gate:
        return gate
    try:
        pid = int(product_id or request.form.get("product_id", 0))
    except (TypeError, ValueError):
        pid = 0
    cart_data = _get_cart()
    if str(pid) in cart_data:
        cart_data[str(pid)] = max(0, cart_data[str(pid)] - 1)
        if cart_data[str(pid)] == 0:
            cart_data.pop(str(pid))
    session.modified = True
    flash("Adet güncellendi.", "info")
    return redirect(url_for("customer_cart"))


@customer_bp.route("/customer/cart/apply_coupon", methods=["POST"])
@login_required
def apply_coupon():
    gate = customer_required()
    if gate:
        return gate
    code = (request.form.get("coupon_code") or "").strip()
    if not code:
        flash("Kupon kodu girin.", "warning")
        return redirect(url_for("customer_cart"))
    cart_data = _get_cart()
    subtotal, _, _, _ = _calculate_cart(cart_data, None, current_user.id)
    coupon = Coupon.query.filter_by(code=code, is_active=True).first()
    if not coupon:
        flash("Kupon bulunamadı veya aktif değil.", "danger")
        session.pop("coupon", None)
        return redirect(url_for("customer_cart"))
    now = datetime.utcnow()
    if coupon.valid_from and coupon.valid_from > now:
        flash("Kupon henüz geçerli değil.", "danger")
        session.pop("coupon", None)
        return redirect(url_for("customer_cart"))
    if coupon.valid_to and coupon.valid_to < now:
        flash("Kupon süresi doldu.", "danger")
        session.pop("coupon", None)
        return redirect(url_for("customer_cart"))
    if subtotal < float(coupon.min_order_amount or 0):
        flash("Kupon için sepet tutarı yetersiz.", "warning")
        return redirect(url_for("customer_cart"))
    if coupon.max_usage_per_user:
        usage = UserCoupon.query.filter_by(user_id=current_user.id, coupon_id=coupon.id).first()
        if usage and usage.usage_count >= coupon.max_usage_per_user:
            flash("Kupon kullanım hakkınız dolmuş.", "warning")
            session.pop("coupon", None)
            return redirect(url_for("customer_cart"))

    session["coupon"] = {"id": coupon.id, "code": coupon.code}
    flash("Kupon uygulandı.", "success")
    return redirect(url_for("customer_cart"))


@customer_bp.route("/customer/cart/remove_coupon", methods=["POST"])
@login_required
def remove_coupon():
    session.pop("coupon", None)
    flash("Kupon kaldırıldı.", "info")
    return redirect(url_for("customer_cart"))


@customer_bp.route("/customer/order/summary", methods=["GET", "POST"], endpoint="customer_order_summary")
@login_required
def order_summary():
    gate = customer_required()
    if gate:
        return gate
    cart_data = _get_cart()
    items = []
    total = 0
    for pid, qty in cart_data.items():
        product = Product.query.get(int(pid))
        if not product:
            continue
        subtotal = float(product.price) * qty
        total += subtotal
        items.append({"id": product.id, "name": product.name, "quantity": qty, "total_price": subtotal})
    totals = {"subtotal": total, "discount": 0, "total": total}
    context = {
        "selected_address": "Adres bilgisi",
        "restaurant": items[0] if items else None,
        "order_items": items,
        "totals": totals,
        "order": {"status": OrderStatus.PENDING},
        "progress_percent": 20,
    }
    return render_template("customer/order_summary.html", **context)


@customer_bp.route("/customer/order/confirm", methods=["POST"])
@login_required
def order_confirm():
    gate = customer_required()
    if gate:
        return gate
    return redirect(url_for("customer_order_summary"))


@customer_bp.route("/customer/order/complete", methods=["POST"])
@login_required
def order_complete():
    gate = customer_required()
    if gate:
        return gate
    cart_data = _get_cart()
    if not cart_data:
        flash("Sepet boş.", "warning")
        return redirect(url_for("customer_cart"))
    # Basit sipariş oluşturma (örnek)
    first_product = Product.query.get(int(next(iter(cart_data.keys()))))
    if not first_product:
        flash("Cart has invalid items.", "danger")
        return redirect(url_for("customer_cart"))
    restaurant_id = first_product.restaurant_id
    branch = _get_branch_for_restaurant(restaurant_id)
    if not branch:
        flash("Bu restoran için aktif bir şube tanımlı değil.", "danger")
        return redirect(url_for("customer_cart"))

    # Ensure we have a user address (schema requires not-null address_id)
    address = _ensure_user_address(current_user.id, branch.neighborhood_id)

    order = Order(user_id=current_user.id, branch_id=branch.id, address_id=address.id, total_amount=0, final_amount=0)
    db.session.add(order)
    db.session.flush()
    subtotal = 0
    for pid, qty in cart_data.items():
        product = Product.query.get(int(pid))
        if not product:
            continue
        item_total = float(product.price) * qty
        subtotal += item_total
        db.session.add(OrderItem(order_id=order.id, product_id=product.id, quantity=qty, unit_price=product.price))
    # Apply coupon if any
    coupon_info = session.get("coupon")
    subtotal_calc, discount, total, coupon_obj = _calculate_cart(cart_data, coupon_info, current_user.id)
    order.total_amount = subtotal_calc
    order.final_amount = total
    if coupon_obj:
        order.coupon_id = coupon_obj.id
        usage = UserCoupon.query.filter_by(user_id=current_user.id, coupon_id=coupon_obj.id).first()
        if not usage:
            usage = UserCoupon(user_id=current_user.id, coupon_id=coupon_obj.id, usage_count=0)
            db.session.add(usage)
        usage.usage_count += 1
    # initial status history
    db.session.add(
        OrderStatusHistory(
            order_id=order.id,
            old_status=OrderStatus.PENDING,
            new_status=OrderStatus.PENDING,
            changed_by_user_id=current_user.id,
        )
    )
    db.session.commit()
    session["cart"] = {}
    session.pop("coupon", None)
    flash("Sipariş oluşturuldu.", "success")
    return redirect(url_for("customer_orders"))


@customer_bp.route("/customer/orders", endpoint="customer_orders")
@login_required
def orders():
    gate = customer_required()
    if gate:
        return gate
    status_filter = request.args.get("status")
    query = Order.query.filter_by(user_id=current_user.id)
    if status_filter and is_valid_status(status_filter):
        query = query.filter(Order.status == status_filter)
    else:
        status_filter = ""
    page = request.args.get("page", 1, type=int)
    per_page = 10
    orders_list, page, pages, total = paginate(query.order_by(Order.id.desc()), page, per_page)
    return render_template("customer/orders.html", orders=orders_list, status_filter=status_filter, page=page, pages=pages)


@customer_bp.route("/customer/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    gate = customer_required()
    if gate:
        return gate
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash("Bu sipariş size ait değil.", "danger")
        return redirect(url_for("customer_orders"))
    review = Review.query.filter_by(order_id=order.id, user_id=current_user.id).first()
    status_history = OrderStatusHistory.query.filter_by(order_id=order.id).order_by(OrderStatusHistory.changed_at.desc()).all()
    return render_template("customer/order_detail.html", order=order, review=review, status_history=status_history)


@customer_bp.route("/customer/orders/<int:order_id>/review", methods=["POST"])
@login_required
def add_review(order_id):
    gate = customer_required()
    if gate:
        return gate
    order = Order.query.get_or_404(order_id)
    existing = Review.query.filter_by(order_id=order.id, user_id=current_user.id).first()
    if existing:
        flash("Review already exists.", "warning")
        return redirect(url_for("customer_orders"))
    rating = int(request.form.get("rating", 5))
    comment = request.form.get("comment")
    restaurant_id = order.branch.restaurant_id if order.branch else None
    review = Review(order_id=order.id, user_id=current_user.id, restaurant_id=restaurant_id, rating=rating, comment=comment)
    db.session.add(review)
    db.session.commit()
    flash("Yorum eklendi.", "success")
    return redirect(url_for("customer_orders"))


@customer_bp.route("/customer/support", endpoint="customer_support")
@login_required
def support():
    gate = customer_required()
    if gate:
        return gate
    tickets = []
    messages = []
    orders_list = Order.query.filter_by(user_id=current_user.id).all()
    return render_template("customer/support_tickets.html", tickets=tickets, messages=messages, orders=orders_list)


@customer_bp.route("/customer/support/new", methods=["POST"])
@login_required
def support_new():
    gate = customer_required()
    if gate:
        return gate
    flash("Destek talebi alındı (örnek).", "info")
    return redirect(url_for("customer_support"))


@customer_bp.route("/customer/support/send", methods=["POST"])
@login_required
def support_send():
    gate = customer_required()
    if gate:
        return gate
    flash("Mesaj gönderildi (örnek).", "info")
    return redirect(url_for("customer_support"))


@customer_bp.route("/customer/favorites", endpoint="customer_favorites")
@login_required
def favorites():
    gate = customer_required()
    if gate:
        return gate
    fav_restaurants = (
        Restaurant.query.join(FavoriteRestaurant, FavoriteRestaurant.restaurant_id == Restaurant.id)
        .filter(FavoriteRestaurant.user_id == current_user.id)
        .all()
    )
    fav_products = (
        Product.query.join(FavoriteProduct, FavoriteProduct.product_id == Product.id)
        .filter(FavoriteProduct.user_id == current_user.id, Product.is_active == True)
        .all()
    )
    return render_template("customer/favorites.html", fav_restaurants=fav_restaurants, fav_products=fav_products)


@customer_bp.route("/customer/favorites/restaurants/<int:restaurant_id>/toggle", methods=["POST"])
@login_required
def toggle_favorite_restaurant(restaurant_id):
    gate = customer_required()
    if gate:
        return gate
    existing = FavoriteRestaurant.query.filter_by(user_id=current_user.id, restaurant_id=restaurant_id).first()
    if existing:
        db.session.delete(existing)
        flash("Restoran favorilerden çıkarıldı.", "info")
    else:
        db.session.add(FavoriteRestaurant(user_id=current_user.id, restaurant_id=restaurant_id))
        flash("Restoran favorilere eklendi.", "success")
    db.session.commit()
    return _redirect_back(default_endpoint="customer_restaurants")


@customer_bp.route("/customer/favorites/products/<int:product_id>/toggle", methods=["POST"])
@login_required
def toggle_favorite_product(product_id):
    gate = customer_required()
    if gate:
        return gate
    existing = FavoriteProduct.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        db.session.delete(existing)
        flash("Ürün favorilerden çıkarıldı.", "info")
    else:
        db.session.add(FavoriteProduct(user_id=current_user.id, product_id=product_id))
        flash("Ürün favorilere eklendi.", "success")
    db.session.commit()
    return _redirect_back(default_endpoint="customer_restaurants")


@customer_bp.route("/customer/addresses", methods=["GET", "POST"], endpoint="customer_addresses")
@login_required
def addresses():
    gate = customer_required()
    if gate:
        return gate
    if request.method == "POST":
        title = (request.form.get("title") or "").strip() or "Adres"
        address_line = (request.form.get("address_line") or "").strip()
        neighborhood_id = int(request.form.get("neighborhood_id") or 0)
        neighborhood_name = (request.form.get("neighborhood_name") or "").strip()
        if not neighborhood_id and neighborhood_name:
            city = City.query.filter_by(name="Istanbul").first()
            if not city:
                city = City(name="Istanbul")
                db.session.add(city)
                db.session.flush()
            district = District.query.filter_by(city_id=city.id, name="Merkez").first()
            if not district:
                district = District(city_id=city.id, name="Merkez")
                db.session.add(district)
                db.session.flush()
            neighborhood = Neighborhood.query.filter_by(district_id=district.id, name=neighborhood_name).first()
            if not neighborhood:
                neighborhood = Neighborhood(district_id=district.id, name=neighborhood_name)
                db.session.add(neighborhood)
                db.session.flush()
            neighborhood_id = neighborhood.id
        if not address_line or not neighborhood_id:
            flash("Adres ve mahalle zorunlu.", "danger")
        else:
            # unset previous default if new default chosen
            make_default = bool(request.form.get("is_default"))
            if make_default:
                UserAddress.query.filter_by(user_id=current_user.id, is_default=True).update({"is_default": False})
            addr = UserAddress(
                user_id=current_user.id,
                neighborhood_id=neighborhood_id,
                title=title,
                address_line=address_line,
                is_default=make_default,
            )
            db.session.add(addr)
            db.session.commit()
            flash("Adres eklendi.", "success")
            return redirect(url_for("customer_addresses"))
    neighborhoods = Neighborhood.query.all()
    addresses = UserAddress.query.filter_by(user_id=current_user.id).all()
    return render_template("customer/addresses.html", addresses=addresses, neighborhoods=neighborhoods)
