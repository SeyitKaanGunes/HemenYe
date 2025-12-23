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
    CuisineType,
    RestaurantCuisine,
    Coupon,
    UserCoupon,
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
    Review,
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


def add_cuisines(restaurant, cuisine_names):
    for cuisine_name in cuisine_names:
        cuisine, _ = get_or_create(CuisineType, name=cuisine_name)
        get_or_create(RestaurantCuisine, restaurant_id=restaurant.id, cuisine_id=cuisine.id)


def create_sample_order(user, branch, address, items, status):
    total = 0
    order = Order(
        user_id=user.id,
        branch_id=branch.id,
        address_id=address.id,
        status=status,
        total_amount=0,
        final_amount=0,
    )
    db.session.add(order)
    db.session.flush()
    for product, quantity in items:
        total += float(product.price) * quantity
        db.session.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                unit_price=product.price,
                quantity=quantity,
            )
        )
    order.total_amount = total
    order.final_amount = total
    db.session.add(
        OrderStatusHistory(
            order_id=order.id,
            old_status=OrderStatus.PENDING,
            new_status=status,
            changed_by_user_id=user.id,
        )
    )
    return order


def create_review(order, restaurant_id, user_id, rating, comment):
    existing = Review.query.filter_by(order_id=order.id).first()
    if existing:
        return existing
    review = Review(
        order_id=order.id,
        user_id=user_id,
        restaurant_id=restaurant_id,
        rating=rating,
        comment=comment,
    )
    db.session.add(review)
    return review


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
        owner_two, _ = get_or_create(
            User,
            email="owner2@example.com",
            defaults={
                "name": "Owner Two",
                "password_hash": generate_password_hash("ownerpass"),
                "role": UserRole.RESTAURANT_OWNER,
            },
        )
        owner_three, _ = get_or_create(
            User,
            email="owner3@example.com",
            defaults={
                "name": "Owner Three",
                "password_hash": generate_password_hash("ownerpass"),
                "role": UserRole.RESTAURANT_OWNER,
            },
        )
        customer_two, _ = get_or_create(
            User,
            email="customer2@example.com",
            defaults={
                "name": "Customer Two",
                "password_hash": generate_password_hash("customerpass"),
                "role": UserRole.CUSTOMER,
            },
        )
        customer_three, _ = get_or_create(
            User,
            email="customer3@example.com",
            defaults={
                "name": "Customer Three",
                "password_hash": generate_password_hash("customerpass"),
                "role": UserRole.CUSTOMER,
            },
        )
        customer_four, _ = get_or_create(
            User,
            email="customer4@example.com",
            defaults={
                "name": "Customer Four",
                "password_hash": generate_password_hash("customerpass"),
                "role": UserRole.CUSTOMER,
            },
        )
        admin_user, _ = get_or_create(
            User,
            email="admin@example.com",
            defaults={
                "name": "Admin",
                "password_hash": generate_password_hash("adminpass"),
                "role": UserRole.ADMIN,
            },
        )

                # Address hierarchy (sample)
        city_istanbul, _ = get_or_create(City, name="Istanbul")
        district_kadikoy, _ = get_or_create(District, city_id=city_istanbul.id, name="Kadikoy")
        neighborhood_moda, _ = get_or_create(Neighborhood, district_id=district_kadikoy.id, name="Moda")
        district_besiktas, _ = get_or_create(District, city_id=city_istanbul.id, name="Besiktas")
        neighborhood_levent, _ = get_or_create(Neighborhood, district_id=district_besiktas.id, name="Levent")
        neighborhood_etiler, _ = get_or_create(Neighborhood, district_id=district_besiktas.id, name="Etiler")

        city_ankara, _ = get_or_create(City, name="Ankara")
        district_cankaya, _ = get_or_create(District, city_id=city_ankara.id, name="Cankaya")
        neighborhood_kizilay, _ = get_or_create(Neighborhood, district_id=district_cankaya.id, name="Kizilay")
        neighborhood_balgat, _ = get_or_create(Neighborhood, district_id=district_cankaya.id, name="Balgat")

        city_izmir, _ = get_or_create(City, name="Izmir")
        district_konak, _ = get_or_create(District, city_id=city_izmir.id, name="Konak")
        neighborhood_alsancak, _ = get_or_create(Neighborhood, district_id=district_konak.id, name="Alsancak")
        neighborhood_goztepe, _ = get_or_create(Neighborhood, district_id=district_konak.id, name="Goztepe")

        # Restaurants with menus
        restaurants = [
            {
                "name": "Deneme Lokanta",
                "owner": owner,
                "neighborhood": neighborhood_moda,
                "phone": "+90 555 000 0000",
                "tax_number": "TN123",
                "min_order": 50,
                "menu": {
                    "Pizzalar": [
                        {"name": "Margarita", "desc": "Mozzarella, domates, feslegen", "price": 120},
                        {"name": "Sucuklu", "desc": "Bol sucuk, kasar", "price": 135},
                    ],
                    "Icecekler": [
                        {"name": "Kola", "desc": "33cl soguk", "price": 25},
                        {"name": "Ayran", "desc": "Taze ayran", "price": 15},
                    ],
                },
            },
            {
                "name": "Burger Station",
                "owner": owner,
                "neighborhood": neighborhood_levent,
                "phone": "+90 555 111 2222",
                "tax_number": "TN456",
                "min_order": 70,
                "menu": {
                    "Burgerler": [
                        {"name": "Klasik Burger", "desc": "140g kofte, cheddar, karamelize sogan", "price": 160},
                        {"name": "Double Burger", "desc": "Cift kofte, cift peynir", "price": 190},
                    ],
                    "Yan Urunler": [
                        {"name": "Patates Kizartmasi", "desc": "Citir patates", "price": 45},
                    ],
                    "Icecekler": [
                        {"name": "Gazoz", "desc": "Cam sise", "price": 22},
                    ],
                },
            },
            {
                "name": "Sushi Nova",
                "owner": owner_two,
                "neighborhood": neighborhood_moda,
                "phone": "+90 555 333 4444",
                "tax_number": "TN789",
                "min_order": 120,
                "menu": {
                    "Roll": [
                        {"name": "California Roll", "desc": "Yengec, avokado, susam", "price": 175},
                        {"name": "Spicy Salmon Roll", "desc": "Acili somon, salatalik", "price": 195},
                    ],
                    "Sicak": [
                        {"name": "Ramen", "desc": "Miso bazli ramen", "price": 210},
                    ],
                },
            },
            {
                "name": "VeganVibe",
                "owner": owner_two,
                "neighborhood": neighborhood_alsancak,
                "phone": "+90 555 555 6666",
                "tax_number": "TN321",
                "min_order": 80,
                "menu": {
                    "Bowllar": [
                        {"name": "Falafel Bowl", "desc": "Humus, falafel, kinoali sebze", "price": 155},
                    ],
                    "Burger": [
                        {"name": "Beyond Burger", "desc": "Bitkisel burger, avokado", "price": 175},
                    ],
                    "Tatli": [
                        {"name": "Chia Puding", "desc": "Badem sutlu, kakaolu", "price": 70},
                    ],
                },
            },
            {
                "name": "Anadolu Kebap",
                "owner": owner_three,
                "neighborhood": neighborhood_kizilay,
                "phone": "+90 555 777 8888",
                "tax_number": "TN654",
                "min_order": 90,
                "menu": {
                    "Kebaplar": [
                        {"name": "Adana Kebap", "desc": "Kozde acili adana", "price": 210},
                        {"name": "Urfa Kebap", "desc": "Acisiz urfa", "price": 205},
                    ],
                    "Pideler": [
                        {"name": "Kiymali Pide", "desc": "Ince hamur", "price": 120},
                    ],
                    "Icecekler": [
                        {"name": "Salgam", "desc": "Acili salgam", "price": 20},
                    ],
                },
            },
            {
                "name": "Tatli Dunyasi",
                "owner": owner,
                "neighborhood": neighborhood_balgat,
                "phone": "+90 555 888 9999",
                "tax_number": "TN852",
                "min_order": 60,
                "menu": {
                    "Tatli": [
                        {"name": "Baklava", "desc": "Fistikli baklava", "price": 95},
                        {"name": "Kunefe", "desc": "Antep peyniri", "price": 110},
                    ],
                    "Icecek": [
                        {"name": "Cay", "desc": "Demli cay", "price": 10},
                        {"name": "Turk Kahvesi", "desc": "Sade", "price": 30},
                    ],
                },
            },
            {
                "name": "Kumru Kose",
                "owner": owner_two,
                "neighborhood": neighborhood_alsancak,
                "phone": "+90 555 444 1212",
                "tax_number": "TN963",
                "min_order": 55,
                "menu": {
                    "Kumru": [
                        {"name": "Sucuklu Kumru", "desc": "Kasar ve sucuk", "price": 90},
                        {"name": "Kasarli Kumru", "desc": "Bol kasar", "price": 85},
                    ],
                    "Sandvicler": [
                        {"name": "Tavuklu Sandvic", "desc": "Izgara tavuk", "price": 75},
                    ],
                    "Icecekler": [
                        {"name": "Limonata", "desc": "Ev yapimi", "price": 25},
                    ],
                },
            },
            {
                "name": "Kahve Atolyesi",
                "owner": owner_three,
                "neighborhood": neighborhood_etiler,
                "phone": "+90 555 232 3434",
                "tax_number": "TN147",
                "min_order": 40,
                "menu": {
                    "Kahveler": [
                        {"name": "Latte", "desc": "Sutlu latte", "price": 65},
                        {"name": "Americano", "desc": "Klasik americano", "price": 55},
                    ],
                    "Tatli": [
                        {"name": "Cheesecake", "desc": "Frambuazli", "price": 85},
                    ],
                    "Atistirmalik": [
                        {"name": "Cookie", "desc": "Cikolata parcalari", "price": 35},
                    ],
                },
            },
        ]

        created_list = []

        created_map = {}
        for r in restaurants:
            rest = create_restaurant(
                owner_id=r["owner"].id,
                neighborhood_id=r["neighborhood"].id,
                name=r["name"],
                phone=r["phone"],
                tax_number=r["tax_number"],
                min_order=r["min_order"],
                menu=r["menu"],
            )
            created_list.append(rest)
            created_map[rest.name] = rest

        cuisine_map = {
            "Deneme Lokanta": ["Pizza", "Italian"],
            "Burger Station": ["Burger", "American"],
            "Sushi Nova": ["Japanese", "Sushi"],
            "VeganVibe": ["Vegan"],
            "Anadolu Kebap": ["Turkish", "Kebab"],
            "Tatli Dunyasi": ["Dessert"],
            "Kumru Kose": ["Turkish", "Street Food"],
            "Kahve Atolyesi": ["Cafe", "Dessert"],
        }
        for rest_name, cuisines in cuisine_map.items():
            rest = created_map.get(rest_name)
            if rest:
                add_cuisines(rest, cuisines)

        extra_branches = [
            (created_map.get("Burger Station"), neighborhood_etiler, "Burger Station Etiler Subesi", "+90 555 111 3333", 90),
            (created_map.get("Anadolu Kebap"), neighborhood_balgat, "Anadolu Kebap Balgat Subesi", "+90 555 777 8899", 95),
            (created_map.get("Kahve Atolyesi"), neighborhood_levent, "Kahve Atolyesi Levent Subesi", "+90 555 232 3535", 45),
        ]
        for rest, neighborhood_item, address_line, phone, min_order in extra_branches:
            if not rest or not neighborhood_item:
                continue
            get_or_create(
                RestaurantBranch,
                restaurant_id=rest.id,
                address_line=address_line,
                defaults={
                    "neighborhood_id": neighborhood_item.id,
                    "phone": phone,
                    "min_order_amount": min_order,
                    "is_active": True,
                },
            )

        # Default addresses
        address_map = {}
        default_addr, _ = get_or_create(
            UserAddress,
            user_id=customer.id,
            title="Ev",
            neighborhood_id=neighborhood_moda.id,
            defaults={"address_line": "Ornek Mah. Deneme Sk. No:2", "is_default": True},
        )
        address_map[customer.id] = default_addr
        addr_two, _ = get_or_create(
            UserAddress,
            user_id=customer_two.id,
            title="Ev",
            neighborhood_id=neighborhood_levent.id,
            defaults={"address_line": "Levent Cd. No:12", "is_default": True},
        )
        address_map[customer_two.id] = addr_two
        addr_three, _ = get_or_create(
            UserAddress,
            user_id=customer_three.id,
            title="Ev",
            neighborhood_id=neighborhood_kizilay.id,
            defaults={"address_line": "Kizilay Sk. No:4", "is_default": True},
        )
        address_map[customer_three.id] = addr_three
        addr_four, _ = get_or_create(
            UserAddress,
            user_id=customer_four.id,
            title="Ev",
            neighborhood_id=neighborhood_alsancak.id,
            defaults={"address_line": "Alsancak Mah. No:7", "is_default": True},
        )
        address_map[customer_four.id] = addr_four

        # Favorites for customers
        customer_list = [customer, customer_two, customer_three, customer_four]
        for idx, cust in enumerate(customer_list):
            for rest in created_list[idx:idx + 2]:
                get_or_create(FavoriteRestaurant, user_id=cust.id, restaurant_id=rest.id)
            if created_list:
                sample_rest = created_list[idx % len(created_list)]
                products = Product.query.filter_by(restaurant_id=sample_rest.id).limit(2).all()
                for product in products:
                    get_or_create(FavoriteProduct, user_id=cust.id, product_id=product.id)

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

        # Sample orders for status history
        statuses = [
            OrderStatus.PENDING,
            OrderStatus.ACCEPTED,
            OrderStatus.PREPARING,
            OrderStatus.ON_THE_WAY,
        ]
        for idx, cust in enumerate(customer_list):
            if not created_list:
                continue
            address = address_map.get(cust.id)
            rest = created_list[idx % len(created_list)]
            branch = RestaurantBranch.query.filter_by(restaurant_id=rest.id).first()
            products = Product.query.filter_by(restaurant_id=rest.id).limit(2).all()
            if not address or not branch or not products:
                continue
            items = [(products[0], 1)]
            if len(products) > 1:
                items.append((products[1], 2))
            create_sample_order(cust, branch, address, items, statuses[idx % len(statuses)])

        # Reviews / ratings for restaurants
        review_ratings = [5, 4, 4, 3, 5, 4]
        review_comments = [
            "Lezzetli ve sicak geldi.",
            "Hizli teslimat, tavsiye ederim.",
            "Porsiyon gayet iyiydi.",
            "Fiyat/performans basarili.",
            "Tekrar siparis ederim.",
            "Urunler taze ve lezzetliydi.",
        ]
        existing_reviewed = {rid for (rid,) in db.session.query(Review.restaurant_id).distinct().all()}
        for idx, rest in enumerate(created_list):
            if rest.id in existing_reviewed:
                continue
            branch = RestaurantBranch.query.filter_by(restaurant_id=rest.id).first()
            products = Product.query.filter_by(restaurant_id=rest.id).limit(1).all()
            cust = customer_list[idx % len(customer_list)]
            address = address_map.get(cust.id)
            if not branch or not products or not address:
                continue
            order = create_sample_order(cust, branch, address, [(products[0], 1)], OrderStatus.DELIVERED)
            rating = review_ratings[idx % len(review_ratings)]
            comment = review_comments[idx % len(review_comments)]
            create_review(order, rest.id, cust.id, rating, comment)

        db.session.commit()

        print("Seed tamam.")
        print("Owner logins: owner@example.com, owner2@example.com, owner3@example.com / ownerpass")
        print("Customer logins: customer@example.com, customer2@example.com, customer3@example.com, customer4@example.com / customerpass")
        print("Admin login: admin@example.com / adminpass")
        print("Created restaurants:")
        for rest in created_list:
            print(f"- {rest.name} (ID: {rest.id})")


if __name__ == "__main__":
    seed()
