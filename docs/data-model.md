# Data Model (HemenYe)

## Overview
Primary entities are users (customers, restaurant owners, admins), restaurants and branches, products/categories, and orders. The model supports reviews, favorites, coupons, and support tickets.

## Core tables and relationships
- User: users with roles; owns restaurants (restaurant_owner), places orders (customer), opens support tickets.
- Restaurant: belongs to a user (owner); has branches, categories, products, reviews, support tickets.
- RestaurantBranch: belongs to a restaurant; links orders to a physical location.
- ProductCategory: belongs to a restaurant; parent-child category hierarchy.
- Product: belongs to a restaurant and a category; participates in order items.
- Order: belongs to a user and a branch; has order items, status history, optional coupon.
- OrderItem: belongs to an order and a product; stores unit price and quantity.
- Review: belongs to an order, user, and restaurant; optional owner reply.
- UserAddress: belongs to a user; tied to a neighborhood (city > district > neighborhood).
- CuisineType + RestaurantCuisine: many-to-many for restaurant cuisines.
- Coupon + UserCoupon: coupon usage tracking per user.
- SupportTicket + SupportMessage: support workflow with messages.
- Favorites: FavoriteRestaurant and FavoriteProduct for user favorites.

## Key constraints (selected)
- User.email is unique.
- ProductCategory.restaurant_id and Product.restaurant_id are required.
- Order links user, branch, address; OrderItem links order and product.
- Review.order_id is unique (one review per order).

## Normalization notes
- 1NF: all fields are atomic (no repeating groups).
- 2NF: non-key attributes depend on full primary keys (composite tables like favorites).
- 3NF: non-key attributes depend only on keys; reference data (cities/districts/neighborhoods, cuisines) is separated.

## ER diagram
- Source: `ERdiagram.puml`
- To render PNG locally (PlantUML):
  - `java -jar plantuml.jar ERdiagram.puml`
