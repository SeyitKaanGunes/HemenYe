# seed_mysql.py - Minimal MySQL seed for local dev (parolasız root varsayılanıyla)
from datetime import datetime
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import (
    City,
    District,
    Neighborhood,
    User,
    Restaurant,
    RestaurantBranch,
    ProductCategory,
    Product,
    UserRole,
    FavoriteRestaurant,
    FavoriteProduct,
    Coupon,
    UserCoupon,
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
    UserAddress,
)


def get_or_create(model, defaults=None, **filters):
    """Simple get_or_create helper."""
    defaults = defaults or {}
    instance = model.query.filter_by(**filters).first()
    if instance:
        return instance, False
    params = {**filters, **defaults}
    instance = model(**params)
    db.session.add(instance)
    db.session.flush()  # assign PKs
    return instance, True


def create_restaurant(owner_id, neighborhood_id, name, phone, tax_number, min_order, menu):
    restaurant, _ = get_or_create(
        Restaurant,
        name=name,
        defaults={
            "owner_id": owner_id,
            "phone": phone,
            "tax_number": tax_number,
            "is_active": True,
        },
    )
    get_or_create(
        RestaurantBranch,
        restaurant_id=restaurant.id,
        address_line=f"{name} Mah. No:1",
        defaults={
            "neighborhood_id": neighborhood_id,
            "phone": phone,
            "min_order_amount": min_order,
            "is_active": True,
        },
    )

    for category_name, products in menu.items():
        cat, _ = get_or_create(
            ProductCategory,
            restaurant_id=restaurant.id,
            name=category_name,
        )
        for p in products:
            get_or_create(
                Product,
                restaurant_id=restaurant.id,
                category_id=cat.id,
                name=p["name"],
                defaults={"description": p["desc"], "price": p["price"], "is_active": True},
            )
    return restaurant


def seed():
    app = create_app()
    with app.app_context():
        # Users
        owner, owner_created = get_or_create(
            User,
            email="owner@example.com",
            defaults={
                "name": "Restoran Sahibi",
                "password_hash": generate_password_hash("ownerpass"),
                "role": UserRole.RESTAURANT_OWNER,
            },
        )
        customer, customer_created = get_or_create(
            User,
            email="customer@example.com",
            defaults={
                "name": "Müşteri",
                "password_hash": generate_password_hash("customerpass"),
                "role": UserRole.CUSTOMER,
            },
        )

        # Address hierarchy (minimal)
        city, _ = get_or_create(City, name="Istanbul")
        district, _ = get_or_create(District, city_id=city.id, name="Kadikoy")
        neighborhood, _ = get_or_create(Neighborhood, district_id=district.id, name="Moda")

        # Restaurants with menus
        restaurants = [
            {
                "name": "Deneme Lokanta",
                "phone": "+90 555 000 0000",
                "tax_number": "TN123",
                "min_order": 50,
                "menu": {
                    "Pizzalar": [
                        {"name": "Margarita", "desc": "Mozzarella, domates, fesleğen", "price": 120},
                        {"name": "Sucuklu", "desc": "Bol sucuk, kaşar", "price": 135},
                    ],
                    "İçecekler": [
                        {"name": "Kola", "desc": "33cl soğuk", "price": 25},
                        {"name": "Ayran", "desc": "Taze ayran", "price": 15},
                    ],
                },
            },
            {
                "name": "Burger Station",
                "phone": "+90 555 111 2222",
                "tax_number": "TN456",
                "min_order": 70,
                "menu": {
                    "Burgerler": [
                        {"name": "Klasik Burger", "desc": "140g köfte, cheddar, karamelize soğan", "price": 160},
                        {"name": "Double Burger", "desc": "Çift köfte, çift peynir", "price": 190},
                    ],
                    "Yan Ürünler": [
                        {"name": "Patates Kızartması", "desc": "Çıtır patates", "price": 45},
                    ],
                    "İçecekler": [
                        {"name": "Gazoz", "desc": "Cam şişe", "price": 22},
                    ],
                },
            },
            {
                "name": "Sushi Nova",
                "phone": "+90 555 333 4444",
                "tax_number": "TN789",
                "min_order": 120,
                "menu": {
                    "Roll": [
                        {"name": "California Roll", "desc": "Yengeç, avokado, susam", "price": 175},
                        {"name": "Spicy Salmon Roll", "desc": "Acılı somon, salatalık", "price": 195},
                    ],
                    "Sıcak": [
                        {"name": "Ramen", "desc": "Miso bazlı ramen", "price": 210},
                    ],
                },
            },
            {
                "name": "VeganVibe",
                "phone": "+90 555 555 6666",
                "tax_number": "TN321",
                "min_order": 80,
                "menu": {
                    "Bowllar": [
                        {"name": "Falafel Bowl", "desc": "Humus, falafel, kinoalı sebze", "price": 155},
                    ],
                    "Burger": [
                        {"name": "Beyond Burger", "desc": "Bitkisel burger, avokado", "price": 175},
                    ],
                    "Tatlı": [
                        {"name": "Chia Puding", "desc": "Badem sütlü, kakaolu", "price": 70},
                    ],
                },
            },
        ]

        created_list = []
        for r in restaurants:
            rest = create_restaurant(
                owner_id=owner.id,
                neighborhood_id=neighborhood.id,
                name=r["name"],
                phone=r["phone"],
                tax_number=r["tax_number"],
                min_order=r["min_order"],
                menu=r["menu"],
            )
            created_list.append(rest)

        # Default address for customer
        default_addr, _ = get_or_create(
            UserAddress,
            user_id=customer.id,
            title="Ev",
            neighborhood_id=neighborhood.id,
            defaults={"address_line": "Örnek Mah. Deneme Sk. No:2", "is_default": True},
        )

        # Favorites for the customer
        for rest in created_list[:2]:
            get_or_create(FavoriteRestaurant, user_id=customer.id, restaurant_id=rest.id)
        pizza = Product.query.filter_by(name="Margarita").first()
        cola = Product.query.filter_by(name="Kola").first()
        if pizza:
            get_or_create(FavoriteProduct, user_id=customer.id, product_id=pizza.id)
        if cola:
            get_or_create(FavoriteProduct, user_id=customer.id, product_id=cola.id)

        # Coupons
        now = datetime.utcnow()
        coupon10, _ = get_or_create(
            Coupon,
            code="INDIRIM10",
            defaults={
                "discount_type": "percent",
                "value": 10,
                "min_order_amount": 50,
                "is_active": True,
                "valid_from": now,
                "valid_to": now.replace(year=now.year + 1),
            },
        )
        coupon20, _ = get_or_create(
            Coupon,
            code="SABIT20",
            defaults={
                "discount_type": "amount",
                "value": 20,
                "min_order_amount": 80,
                "is_active": True,
                "valid_from": now,
                "valid_to": now.replace(year=now.year + 1),
            },
        )
        get_or_create(UserCoupon, user_id=customer.id, coupon_id=coupon10.id, defaults={"usage_count": 0})
        get_or_create(UserCoupon, user_id=customer.id, coupon_id=coupon20.id, defaults={"usage_count": 1})

        # Sample order for status history and price history demo
        if pizza and cola:
            branch = RestaurantBranch.query.filter_by(restaurant_id=pizza.restaurant_id).first()
            order = Order(
                user_id=customer.id,
                branch_id=branch.id,
                address_id=default_addr.id,
                status=OrderStatus.PREPARING,
                total_amount=145,
                final_amount=125,
            )
            db.session.add(order)
            db.session.flush()
            db.session.add(OrderItem(order_id=order.id, product_id=pizza.id, unit_price=120, quantity=1))
            db.session.add(OrderItem(order_id=order.id, product_id=cola.id, unit_price=25, quantity=1))
            db.session.add(
                OrderStatusHistory(
                    order_id=order.id,
                    old_status=OrderStatus.PENDING,
                    new_status=OrderStatus.PREPARING,
                    changed_by_user_id=owner.id,
                )
            )

        db.session.commit()

        print("Seed tamam.")
        if owner_created:
            print("Sahip girişi: owner@example.com / ownerpass")
        if customer_created:
            print("Müşteri girişi: customer@example.com / customerpass")
        print("Oluşturulan restoranlar:")
        for rest in created_list:
            print(f"- {rest.name} (ID: {rest.id})")


if __name__ == "__main__":
    seed()
