# seed.py - Seed sample data for HemenYe backend
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import (
    City,
    CuisineType,
    District,
    FavoriteProduct,
    FavoriteRestaurant,
    Neighborhood,
    Product,
    ProductCategory,
    ProductOption,
    ProductOptionGroup,
    ProductProductOptionGroup,
    Restaurant,
    RestaurantBranch,
    RestaurantCuisine,
    User,
    UserAddress,
)


def get_or_create(model, defaults=None, **kwargs):
    defaults = defaults or {}
    instance = model.query.filter_by(**kwargs).first()
    if instance:
        return instance, False
    params = {**kwargs, **defaults}
    instance = model(**params)
    db.session.add(instance)
    # Flush to assign primary keys so downstream relations can use them
    db.session.flush()
    return instance, True


def seed():
    app = create_app()
    with app.app_context():
        # Users
        owner, created_owner = get_or_create(
            User,
            name="Owner One",
            email="owner@example.com",
            role="restaurant_owner",
            password_hash=generate_password_hash("ownerpass"),
        )
        customer, created_customer = get_or_create(
            User,
            name="Customer One",
            email="customer@example.com",
            role="customer",
            password_hash=generate_password_hash("customerpass"),
        )

        # Address hierarchy
        city, _ = get_or_create(City, name="Istanbul")
        district, _ = get_or_create(District, city_id=city.city_id, name="Kadikoy")
        neighborhood, _ = get_or_create(Neighborhood, district_id=district.district_id, name="Moda")

        # Restaurant and branch
        restaurant, _ = get_or_create(
            Restaurant,
            owner_id=owner.user_id,
            name="Lezzet Duragi",
            defaults={"is_active": 1},
        )
        branch, _ = get_or_create(
            RestaurantBranch,
            restaurant_id=restaurant.restaurant_id,
            neighborhood_id=neighborhood.neighborhood_id,
            defaults={
                "address_line": "Example Street No:1",
                "min_order_amount": 50.00,
                "is_active": 1,
            },
        )

        # Cuisine
        cuisine, _ = get_or_create(CuisineType, name="Pizza")
        rc_link, _ = get_or_create(RestaurantCuisine, restaurant_id=restaurant.restaurant_id, cuisine_id=cuisine.cuisine_id)

        # User address for customer
        user_addr, _ = get_or_create(
            UserAddress,
            user_id=customer.user_id,
            neighborhood_id=neighborhood.neighborhood_id,
            defaults={"title": "Home", "address_line": "Customer Address Line", "is_default": 1},
        )

        # Categories
        cat_pizza, _ = get_or_create(
            ProductCategory,
            restaurant_id=restaurant.restaurant_id,
            name="Pizzas",
        )
        cat_drink, _ = get_or_create(
            ProductCategory,
            restaurant_id=restaurant.restaurant_id,
            name="Drinks",
        )

        # Products
        pizza, _ = get_or_create(
            Product,
            restaurant_id=restaurant.restaurant_id,
            category_id=cat_pizza.category_id,
            name="Margherita",
            defaults={"description": "Classic cheese pizza", "base_price": 120.00, "is_active": 1},
        )
        cola, _ = get_or_create(
            Product,
            restaurant_id=restaurant.restaurant_id,
            category_id=cat_drink.category_id,
            name="Cola",
            defaults={"description": "Chilled cola", "base_price": 25.00, "is_active": 1},
        )

        # Option group and options for pizza
        size_group, _ = get_or_create(
            ProductOptionGroup,
            restaurant_id=restaurant.restaurant_id,
            name="Size",
            defaults={"is_required": 1, "min_select": 1, "max_select": 1},
        )
        small_opt, _ = get_or_create(
            ProductOption,
            option_group_id=size_group.option_group_id,
            name="Small",
            defaults={"extra_price": 0.00, "is_active": 1},
        )
        large_opt, _ = get_or_create(
            ProductOption,
            option_group_id=size_group.option_group_id,
            name="Large",
            defaults={"extra_price": 20.00, "is_active": 1},
        )

        # Link pizza to size option group
        link, _ = get_or_create(
            ProductProductOptionGroup,
            product_id=pizza.product_id,
            option_group_id=size_group.option_group_id,
        )

        # Favorites examples
        fav_rest, _ = get_or_create(FavoriteRestaurant, user_id=customer.user_id, restaurant_id=restaurant.restaurant_id)
        fav_prod, _ = get_or_create(FavoriteProduct, user_id=customer.user_id, product_id=pizza.product_id)

        db.session.commit()

        print("Seed completed.")
        if created_owner:
            print("Owner login: owner@example.com / ownerpass")
        if created_customer:
            print("Customer login: customer@example.com / customerpass")


if __name__ == "__main__":
    seed()
