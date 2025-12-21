# app/models.py - core SQLAlchemy models aligned with the MySQL schema
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Enum, ForeignKey

from app.extensions import db, login_manager


class UserRole:
    CUSTOMER = "customer"
    RESTAURANT_OWNER = "restaurant_owner"
    ADMIN = "admin"


class DiscountType:
    PERCENT = "percent"
    AMOUNT = "amount"


class OrderStatus:
    PENDING = "pending"
    ACCEPTED = "accepted"
    PREPARING = "preparing"
    ON_THE_WAY = "on_the_way"
    DELIVERED = "delivered"
    CANCELED = "canceled"


class TicketStatus:
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class User(db.Model, UserMixin):
    __tablename__ = "User"

    id = db.Column("user_id", db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(Enum(UserRole.CUSTOMER, UserRole.RESTAURANT_OWNER, UserRole.ADMIN, name="user_role"), nullable=False, default=UserRole.CUSTOMER)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    restaurants = db.relationship("Restaurant", back_populates="owner", foreign_keys="Restaurant.owner_id")
    orders = db.relationship("Order", back_populates="user", foreign_keys="Order.user_id")
    reviews = db.relationship("Review", back_populates="user", foreign_keys="Review.user_id")
    support_tickets = db.relationship("SupportTicket", back_populates="user", foreign_keys="SupportTicket.user_id")
    addresses = db.relationship("UserAddress", back_populates="user", foreign_keys="UserAddress.user_id")
    favorite_restaurants = db.relationship("FavoriteRestaurant", back_populates="user", foreign_keys="FavoriteRestaurant.user_id")
    favorite_products = db.relationship("FavoriteProduct", back_populates="user", foreign_keys="FavoriteProduct.user_id")
    coupons = db.relationship("UserCoupon", back_populates="user", foreign_keys="UserCoupon.user_id")
    status_changes = db.relationship("OrderStatusHistory", back_populates="user", foreign_keys="OrderStatusHistory.changed_by_user_id")
    price_changes = db.relationship("ProductPriceHistory", back_populates="user", foreign_keys="ProductPriceHistory.changed_by_user_id")


class Restaurant(db.Model):
    __tablename__ = "Restaurant"

    id = db.Column("restaurant_id", db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, ForeignKey("User.user_id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    tax_number = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)

    owner = db.relationship("User", back_populates="restaurants", foreign_keys=[owner_id])
    branches = db.relationship("RestaurantBranch", back_populates="restaurant", foreign_keys="RestaurantBranch.restaurant_id")
    categories = db.relationship("ProductCategory", back_populates="restaurant", foreign_keys="ProductCategory.restaurant_id")
    products = db.relationship("Product", back_populates="restaurant", foreign_keys="Product.restaurant_id")
    reviews = db.relationship("Review", back_populates="restaurant", foreign_keys="Review.restaurant_id")
    tickets = db.relationship("SupportTicket", back_populates="restaurant", foreign_keys="SupportTicket.restaurant_id")
    favorites = db.relationship("FavoriteRestaurant", back_populates="restaurant", foreign_keys="FavoriteRestaurant.restaurant_id")


class City(db.Model):
    __tablename__ = "City"

    id = db.Column("city_id", db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)


class District(db.Model):
    __tablename__ = "District"

    id = db.Column("district_id", db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, ForeignKey("City.city_id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)

    city = db.relationship("City")


class Neighborhood(db.Model):
    __tablename__ = "Neighborhood"

    id = db.Column("neighborhood_id", db.Integer, primary_key=True)
    district_id = db.Column(db.Integer, ForeignKey("District.district_id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)

    district = db.relationship("District")


class UserAddress(db.Model):
    __tablename__ = "UserAddress"

    id = db.Column("address_id", db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("User.user_id"), nullable=False)
    neighborhood_id = db.Column(db.Integer, ForeignKey("Neighborhood.neighborhood_id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    address_line = db.Column(db.String(500), nullable=False)
    is_default = db.Column(db.Boolean, default=False)

    user = db.relationship("User", back_populates="addresses")
    neighborhood = db.relationship("Neighborhood")


class CuisineType(db.Model):
    __tablename__ = "CuisineType"

    id = db.Column("cuisine_id", db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)


class RestaurantCuisine(db.Model):
    __tablename__ = "RestaurantCuisine"

    restaurant_id = db.Column(db.Integer, ForeignKey("Restaurant.restaurant_id"), primary_key=True)
    cuisine_id = db.Column(db.Integer, ForeignKey("CuisineType.cuisine_id"), primary_key=True)

    restaurant = db.relationship("Restaurant", backref="cuisine_links")
    cuisine = db.relationship("CuisineType")


class RestaurantBranch(db.Model):
    __tablename__ = "RestaurantBranch"

    id = db.Column("branch_id", db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, ForeignKey("Restaurant.restaurant_id"), nullable=False)
    neighborhood_id = db.Column(db.Integer, ForeignKey("Neighborhood.neighborhood_id"), nullable=False)
    address_line = db.Column(db.String(500), nullable=False)
    phone = db.Column(db.String(20))
    min_order_amount = db.Column(db.Numeric(10, 2), default=0)
    is_active = db.Column(db.Boolean, default=True)

    restaurant = db.relationship("Restaurant", back_populates="branches")
    neighborhood = db.relationship("Neighborhood")
    orders = db.relationship("Order", back_populates="branch", foreign_keys="Order.branch_id")


class ProductCategory(db.Model):
    __tablename__ = "ProductCategory"

    id = db.Column("category_id", db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, ForeignKey("Restaurant.restaurant_id"), nullable=False)
    parent_id = db.Column("parent_category_id", db.Integer, ForeignKey("ProductCategory.category_id"))
    name = db.Column(db.String(255), nullable=False)

    restaurant = db.relationship("Restaurant", back_populates="categories")
    products = db.relationship("Product", back_populates="category")
    parent = db.relationship("ProductCategory", remote_side=[id])


class Product(db.Model):
    __tablename__ = "Product"

    id = db.Column("product_id", db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, ForeignKey("Restaurant.restaurant_id"), nullable=False)
    category_id = db.Column(db.Integer, ForeignKey("ProductCategory.category_id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column("base_price", db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    restaurant = db.relationship("Restaurant", back_populates="products", foreign_keys=[restaurant_id])
    category = db.relationship("ProductCategory", back_populates="products", foreign_keys=[category_id])
    order_items = db.relationship("OrderItem", back_populates="product", foreign_keys="OrderItem.product_id")
    favorites = db.relationship("FavoriteProduct", back_populates="product", foreign_keys="FavoriteProduct.product_id")
    price_history = db.relationship("ProductPriceHistory", back_populates="product", foreign_keys="ProductPriceHistory.product_id")


class ProductOptionGroup(db.Model):
    __tablename__ = "ProductOptionGroup"

    id = db.Column("option_group_id", db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, ForeignKey("Restaurant.restaurant_id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    is_required = db.Column(db.Boolean, default=False)
    min_select = db.Column(db.Integer, default=0)
    max_select = db.Column(db.Integer, default=1)

    restaurant = db.relationship("Restaurant")
    options = db.relationship("ProductOption", back_populates="group", foreign_keys="ProductOption.option_group_id")
    products = db.relationship("ProductProductOptionGroup", back_populates="option_group", cascade="all, delete-orphan")


class ProductOption(db.Model):
    __tablename__ = "ProductOption"

    id = db.Column("option_id", db.Integer, primary_key=True)
    option_group_id = db.Column(db.Integer, ForeignKey("ProductOptionGroup.option_group_id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    extra_price = db.Column(db.Numeric(10, 2), default=0)
    is_active = db.Column(db.Boolean, default=True)

    group = db.relationship("ProductOptionGroup", back_populates="options")


class ProductProductOptionGroup(db.Model):
    __tablename__ = "Product_ProductOptionGroup"

    product_id = db.Column(db.Integer, ForeignKey("Product.product_id"), primary_key=True)
    option_group_id = db.Column(db.Integer, ForeignKey("ProductOptionGroup.option_group_id"), primary_key=True)

    product = db.relationship("Product")
    option_group = db.relationship("ProductOptionGroup", back_populates="products")


class Coupon(db.Model):
    __tablename__ = "Coupon"

    id = db.Column("coupon_id", db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_type = db.Column(Enum(DiscountType.PERCENT, DiscountType.AMOUNT, name="discount_type"), nullable=False)
    value = db.Column(db.Numeric(10, 2), nullable=False)
    min_order_amount = db.Column(db.Numeric(10, 2), default=0)
    valid_from = db.Column(db.DateTime)
    valid_to = db.Column(db.DateTime)
    max_usage_per_user = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)

    orders = db.relationship("Order", back_populates="coupon")
    user_coupons = db.relationship("UserCoupon", back_populates="coupon", foreign_keys="UserCoupon.coupon_id")


class Order(db.Model):
    __tablename__ = "Order"

    id = db.Column("order_id", db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("User.user_id"), nullable=False)
    branch_id = db.Column(db.Integer, ForeignKey("RestaurantBranch.branch_id"), nullable=False)
    address_id = db.Column(db.Integer, ForeignKey("UserAddress.address_id"), nullable=False)
    coupon_id = db.Column(db.Integer, ForeignKey("Coupon.coupon_id"))
    status = db.Column(Enum(OrderStatus.PENDING, OrderStatus.ACCEPTED, OrderStatus.PREPARING, OrderStatus.ON_THE_WAY, OrderStatus.DELIVERED, OrderStatus.CANCELED, name="order_status"), default=OrderStatus.PENDING)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    final_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    user = db.relationship("User", back_populates="orders", foreign_keys=[user_id])
    branch = db.relationship("RestaurantBranch", back_populates="orders", foreign_keys=[branch_id])
    items = db.relationship("OrderItem", back_populates="order", foreign_keys="OrderItem.order_id")
    coupon = db.relationship("Coupon", back_populates="orders", foreign_keys=[coupon_id])
    review = db.relationship("Review", back_populates="order", uselist=False, foreign_keys="Review.order_id")
    tickets = db.relationship("SupportTicket", back_populates="order", foreign_keys="SupportTicket.order_id")
    status_history = db.relationship("OrderStatusHistory", back_populates="order", foreign_keys="OrderStatusHistory.order_id")


class OrderItem(db.Model):
    __tablename__ = "OrderItem"

    id = db.Column("order_item_id", db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, ForeignKey("Order.order_id"), nullable=False)
    product_id = db.Column(db.Integer, ForeignKey("Product.product_id"), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product", back_populates="order_items")


class Review(db.Model):
    __tablename__ = "Review"

    id = db.Column("review_id", db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, ForeignKey("Order.order_id"), nullable=False, unique=True)
    user_id = db.Column(db.Integer, ForeignKey("User.user_id"), nullable=False)
    restaurant_id = db.Column(db.Integer, ForeignKey("Restaurant.restaurant_id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order = db.relationship("Order", back_populates="review", foreign_keys=[order_id])
    user = db.relationship("User", back_populates="reviews", foreign_keys=[user_id])
    restaurant = db.relationship("Restaurant", back_populates="reviews", foreign_keys=[restaurant_id])
    reply = db.relationship("ReviewReply", back_populates="review", uselist=False, foreign_keys="ReviewReply.review_id")


class ReviewReply(db.Model):
    __tablename__ = "ReviewReply"

    id = db.Column("reply_id", db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, ForeignKey("Review.review_id"), nullable=False, unique=True)
    owner_id = db.Column(db.Integer, ForeignKey("User.user_id"), nullable=False)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    review = db.relationship("Review", back_populates="reply")
    owner = db.relationship("User")


class SupportTicket(db.Model):
    __tablename__ = "SupportTicket"

    id = db.Column("ticket_id", db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("User.user_id"), nullable=False)
    restaurant_id = db.Column(db.Integer, ForeignKey("Restaurant.restaurant_id"))
    order_id = db.Column(db.Integer, ForeignKey("Order.order_id"))
    status = db.Column(Enum(TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.CLOSED, name="ticket_status"), default=TicketStatus.OPEN)
    subject = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="support_tickets")
    restaurant = db.relationship("Restaurant", back_populates="tickets")
    order = db.relationship("Order", back_populates="tickets")
    messages = db.relationship("SupportMessage", back_populates="ticket")


class SupportMessage(db.Model):
    __tablename__ = "SupportMessage"

    id = db.Column("message_id", db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, ForeignKey("SupportTicket.ticket_id"), nullable=False)
    sender_id = db.Column("sender_user_id", db.Integer, ForeignKey("User.user_id"), nullable=False)
    body = db.Column("message", db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket = db.relationship("SupportTicket", back_populates="messages")
    sender = db.relationship("User")


class UserCoupon(db.Model):
    __tablename__ = "UserCoupon"

    user_id = db.Column(db.Integer, ForeignKey("User.user_id"), primary_key=True)
    coupon_id = db.Column(db.Integer, ForeignKey("Coupon.coupon_id"), primary_key=True)
    usage_count = db.Column(db.Integer, default=0, nullable=False)

    user = db.relationship("User", back_populates="coupons")
    coupon = db.relationship("Coupon", back_populates="user_coupons")


class FavoriteRestaurant(db.Model):
    __tablename__ = "FavoriteRestaurant"

    user_id = db.Column(db.Integer, ForeignKey("User.user_id"), primary_key=True)
    restaurant_id = db.Column(db.Integer, ForeignKey("Restaurant.restaurant_id"), primary_key=True)

    user = db.relationship("User", back_populates="favorite_restaurants")
    restaurant = db.relationship("Restaurant", back_populates="favorites")


class FavoriteProduct(db.Model):
    __tablename__ = "FavoriteProduct"

    user_id = db.Column(db.Integer, ForeignKey("User.user_id"), primary_key=True)
    product_id = db.Column(db.Integer, ForeignKey("Product.product_id"), primary_key=True)

    user = db.relationship("User", back_populates="favorite_products")
    product = db.relationship("Product", back_populates="favorites")


class OrderStatusHistory(db.Model):
    __tablename__ = "OrderStatusHistory"

    id = db.Column("history_id", db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, ForeignKey("Order.order_id"), nullable=False)
    old_status = db.Column(Enum(OrderStatus.PENDING, OrderStatus.ACCEPTED, OrderStatus.PREPARING, OrderStatus.ON_THE_WAY, OrderStatus.DELIVERED, OrderStatus.CANCELED, name="order_status"), nullable=False)
    new_status = db.Column(Enum(OrderStatus.PENDING, OrderStatus.ACCEPTED, OrderStatus.PREPARING, OrderStatus.ON_THE_WAY, OrderStatus.DELIVERED, OrderStatus.CANCELED, name="order_status"), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    changed_by_user_id = db.Column(db.Integer, ForeignKey("User.user_id"), nullable=False)

    order = db.relationship("Order", back_populates="status_history")
    user = db.relationship("User", back_populates="status_changes")


class ProductPriceHistory(db.Model):
    __tablename__ = "ProductPriceHistory"

    id = db.Column("price_history_id", db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, ForeignKey("Product.product_id"), nullable=False)
    old_price = db.Column(db.Numeric(10, 2), nullable=False)
    new_price = db.Column(db.Numeric(10, 2), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    changed_by_user_id = db.Column(db.Integer, ForeignKey("User.user_id"), nullable=False)

    product = db.relationship("Product", back_populates="price_history")
    user = db.relationship("User", back_populates="price_changes")


@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))
