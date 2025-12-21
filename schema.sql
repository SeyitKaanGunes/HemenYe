CREATE TABLE `User` (
  `user_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `phone` VARCHAR(20),
  `role` ENUM('customer','restaurant_owner','admin') NOT NULL DEFAULT 'customer',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `uq_user_email` (`email`),
  KEY `idx_user_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `City` (
  `city_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`city_id`),
  UNIQUE KEY `uq_city_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `District` (
  `district_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `city_id` INT UNSIGNED NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`district_id`),
  UNIQUE KEY `uq_district_city_name` (`city_id`,`name`),
  KEY `idx_district_city` (`city_id`),
  CONSTRAINT `fk_district_city` FOREIGN KEY (`city_id`) REFERENCES `City`(`city_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `Neighborhood` (
  `neighborhood_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `district_id` INT UNSIGNED NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`neighborhood_id`),
  UNIQUE KEY `uq_neighborhood_district_name` (`district_id`,`name`),
  KEY `idx_neighborhood_district` (`district_id`),
  CONSTRAINT `fk_neighborhood_district` FOREIGN KEY (`district_id`) REFERENCES `District`(`district_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `Restaurant` (
  `restaurant_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `owner_id` INT UNSIGNED NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `tax_number` VARCHAR(50),
  `phone` VARCHAR(20),
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`restaurant_id`),
  KEY `idx_restaurant_owner` (`owner_id`),
  CONSTRAINT `fk_restaurant_owner` FOREIGN KEY (`owner_id`) REFERENCES `User`(`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `RestaurantBranch` (
  `branch_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `restaurant_id` INT UNSIGNED NOT NULL,
  `neighborhood_id` INT UNSIGNED NOT NULL,
  `address_line` VARCHAR(500) NOT NULL,
  `phone` VARCHAR(20),
  `min_order_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`branch_id`),
  KEY `idx_branch_restaurant` (`restaurant_id`),
  KEY `idx_branch_neighborhood` (`neighborhood_id`),
  CONSTRAINT `fk_branch_restaurant` FOREIGN KEY (`restaurant_id`) REFERENCES `Restaurant`(`restaurant_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_branch_neighborhood` FOREIGN KEY (`neighborhood_id`) REFERENCES `Neighborhood`(`neighborhood_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `UserAddress` (
  `address_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` INT UNSIGNED NOT NULL,
  `neighborhood_id` INT UNSIGNED NOT NULL,
  `title` VARCHAR(100) NOT NULL,
  `address_line` VARCHAR(500) NOT NULL,
  `is_default` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`address_id`),
  KEY `idx_useraddress_user` (`user_id`),
  KEY `idx_useraddress_neighborhood` (`neighborhood_id`),
  CONSTRAINT `fk_useraddress_user` FOREIGN KEY (`user_id`) REFERENCES `User`(`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_useraddress_neighborhood` FOREIGN KEY (`neighborhood_id`) REFERENCES `Neighborhood`(`neighborhood_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `CuisineType` (
  `cuisine_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`cuisine_id`),
  UNIQUE KEY `uq_cuisine_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `RestaurantCuisine` (
  `restaurant_id` INT UNSIGNED NOT NULL,
  `cuisine_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`restaurant_id`,`cuisine_id`),
  KEY `idx_restaurantcuisine_cuisine` (`cuisine_id`),
  CONSTRAINT `fk_restaurantcuisine_restaurant` FOREIGN KEY (`restaurant_id`) REFERENCES `Restaurant`(`restaurant_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_restaurantcuisine_cuisine` FOREIGN KEY (`cuisine_id`) REFERENCES `CuisineType`(`cuisine_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `ProductCategory` (
  `category_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `restaurant_id` INT UNSIGNED NOT NULL,
  `parent_category_id` INT UNSIGNED DEFAULT NULL,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`category_id`),
  UNIQUE KEY `uq_category_restaurant_name` (`restaurant_id`,`name`),
  KEY `idx_category_parent` (`parent_category_id`),
  CONSTRAINT `fk_category_restaurant` FOREIGN KEY (`restaurant_id`) REFERENCES `Restaurant`(`restaurant_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_category_parent` FOREIGN KEY (`parent_category_id`) REFERENCES `ProductCategory`(`category_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `Product` (
  `product_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `restaurant_id` INT UNSIGNED NOT NULL,
  `category_id` INT UNSIGNED NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT,
  `base_price` DECIMAL(10,2) NOT NULL,
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`product_id`),
  KEY `idx_product_restaurant` (`restaurant_id`),
  KEY `idx_product_category` (`category_id`),
  CONSTRAINT `fk_product_restaurant` FOREIGN KEY (`restaurant_id`) REFERENCES `Restaurant`(`restaurant_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_product_category` FOREIGN KEY (`category_id`) REFERENCES `ProductCategory`(`category_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `ProductOptionGroup` (
  `option_group_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `restaurant_id` INT UNSIGNED NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `is_required` TINYINT(1) NOT NULL DEFAULT 0,
  `min_select` INT NOT NULL DEFAULT 0,
  `max_select` INT NOT NULL DEFAULT 1,
  PRIMARY KEY (`option_group_id`),
  UNIQUE KEY `uq_optiongroup_restaurant_name` (`restaurant_id`,`name`),
  KEY `idx_optiongroup_restaurant` (`restaurant_id`),
  CONSTRAINT `fk_optiongroup_restaurant` FOREIGN KEY (`restaurant_id`) REFERENCES `Restaurant`(`restaurant_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `ProductOption` (
  `option_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `option_group_id` INT UNSIGNED NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `extra_price` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`option_id`),
  UNIQUE KEY `uq_option_group_name` (`option_group_id`,`name`),
  KEY `idx_option_group` (`option_group_id`),
  CONSTRAINT `fk_option_group` FOREIGN KEY (`option_group_id`) REFERENCES `ProductOptionGroup`(`option_group_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `Product_ProductOptionGroup` (
  `product_id` INT UNSIGNED NOT NULL,
  `option_group_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`product_id`,`option_group_id`),
  KEY `idx_ppog_option_group` (`option_group_id`),
  CONSTRAINT `fk_ppog_product` FOREIGN KEY (`product_id`) REFERENCES `Product`(`product_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_ppog_option_group` FOREIGN KEY (`option_group_id`) REFERENCES `ProductOptionGroup`(`option_group_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `Coupon` (
  `coupon_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(50) NOT NULL,
  `discount_type` ENUM('percent','amount') NOT NULL,
  `value` DECIMAL(10,2) NOT NULL,
  `min_order_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `valid_from` DATETIME NOT NULL,
  `valid_to` DATETIME NOT NULL,
  `max_usage_per_user` INT UNSIGNED,
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`coupon_id`),
  UNIQUE KEY `uq_coupon_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `UserCoupon` (
  `user_id` INT UNSIGNED NOT NULL,
  `coupon_id` INT UNSIGNED NOT NULL,
  `usage_count` INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`user_id`,`coupon_id`),
  KEY `idx_usercoupon_coupon` (`coupon_id`),
  CONSTRAINT `fk_usercoupon_user` FOREIGN KEY (`user_id`) REFERENCES `User`(`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_usercoupon_coupon` FOREIGN KEY (`coupon_id`) REFERENCES `Coupon`(`coupon_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `FavoriteRestaurant` (
  `user_id` INT UNSIGNED NOT NULL,
  `restaurant_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`user_id`,`restaurant_id`),
  KEY `idx_favoriterestaurant_restaurant` (`restaurant_id`),
  CONSTRAINT `fk_favoriterestaurant_user` FOREIGN KEY (`user_id`) REFERENCES `User`(`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_favoriterestaurant_restaurant` FOREIGN KEY (`restaurant_id`) REFERENCES `Restaurant`(`restaurant_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `FavoriteProduct` (
  `user_id` INT UNSIGNED NOT NULL,
  `product_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`user_id`,`product_id`),
  KEY `idx_favoriteproduct_product` (`product_id`),
  CONSTRAINT `fk_favoriteproduct_user` FOREIGN KEY (`user_id`) REFERENCES `User`(`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_favoriteproduct_product` FOREIGN KEY (`product_id`) REFERENCES `Product`(`product_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `Order` (
  `order_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` INT UNSIGNED NOT NULL,
  `branch_id` INT UNSIGNED NOT NULL,
  `address_id` INT UNSIGNED NOT NULL,
  `coupon_id` INT UNSIGNED DEFAULT NULL,
  `status` ENUM('pending','accepted','preparing','on_the_way','delivered','canceled') NOT NULL DEFAULT 'pending',
  `total_amount` DECIMAL(10,2) NOT NULL,
  `final_amount` DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (`order_id`),
  KEY `idx_order_user` (`user_id`),
  KEY `idx_order_branch` (`branch_id`),
  KEY `idx_order_address` (`address_id`),
  KEY `idx_order_coupon` (`coupon_id`),
  CONSTRAINT `fk_order_user` FOREIGN KEY (`user_id`) REFERENCES `User`(`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_order_branch` FOREIGN KEY (`branch_id`) REFERENCES `RestaurantBranch`(`branch_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_order_address` FOREIGN KEY (`address_id`) REFERENCES `UserAddress`(`address_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_order_coupon` FOREIGN KEY (`coupon_id`) REFERENCES `Coupon`(`coupon_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `OrderItem` (
  `order_item_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `order_id` INT UNSIGNED NOT NULL,
  `product_id` INT UNSIGNED NOT NULL,
  `unit_price` DECIMAL(10,2) NOT NULL,
  `quantity` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`order_item_id`),
  KEY `idx_orderitem_order` (`order_id`),
  KEY `idx_orderitem_product` (`product_id`),
  CONSTRAINT `fk_orderitem_order` FOREIGN KEY (`order_id`) REFERENCES `Order`(`order_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_orderitem_product` FOREIGN KEY (`product_id`) REFERENCES `Product`(`product_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `Review` (
  `review_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `order_id` INT UNSIGNED NOT NULL,
  `user_id` INT UNSIGNED NOT NULL,
  `restaurant_id` INT UNSIGNED NOT NULL,
  `rating` INT NOT NULL,
  `comment` TEXT,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`review_id`),
  UNIQUE KEY `uq_review_order` (`order_id`),
  KEY `idx_review_user` (`user_id`),
  KEY `idx_review_restaurant` (`restaurant_id`),
  CONSTRAINT `fk_review_order` FOREIGN KEY (`order_id`) REFERENCES `Order`(`order_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_review_user` FOREIGN KEY (`user_id`) REFERENCES `User`(`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_review_restaurant` FOREIGN KEY (`restaurant_id`) REFERENCES `Restaurant`(`restaurant_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `ReviewReply` (
  `reply_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `review_id` INT UNSIGNED NOT NULL,
  `owner_id` INT UNSIGNED NOT NULL,
  `message` TEXT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`reply_id`),
  UNIQUE KEY `uq_reviewreply_review` (`review_id`),
  KEY `idx_reviewreply_owner` (`owner_id`),
  CONSTRAINT `fk_reviewreply_review` FOREIGN KEY (`review_id`) REFERENCES `Review`(`review_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_reviewreply_owner` FOREIGN KEY (`owner_id`) REFERENCES `User`(`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `SupportTicket` (
  `ticket_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` INT UNSIGNED NOT NULL,
  `order_id` INT UNSIGNED DEFAULT NULL,
  `status` ENUM('open','in_progress','resolved','closed') NOT NULL DEFAULT 'open',
  PRIMARY KEY (`ticket_id`),
  KEY `idx_supportticket_user` (`user_id`),
  KEY `idx_supportticket_order` (`order_id`),
  CONSTRAINT `fk_supportticket_user` FOREIGN KEY (`user_id`) REFERENCES `User`(`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_supportticket_order` FOREIGN KEY (`order_id`) REFERENCES `Order`(`order_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `SupportMessage` (
  `message_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `ticket_id` INT UNSIGNED NOT NULL,
  `sender_user_id` INT UNSIGNED NOT NULL,
  `message` TEXT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`message_id`),
  KEY `idx_supportmessage_ticket` (`ticket_id`),
  KEY `idx_supportmessage_sender` (`sender_user_id`),
  CONSTRAINT `fk_supportmessage_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `SupportTicket`(`ticket_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_supportmessage_sender` FOREIGN KEY (`sender_user_id`) REFERENCES `User`(`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `OrderStatusHistory` (
  `history_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `order_id` INT UNSIGNED NOT NULL,
  `old_status` ENUM('pending','accepted','preparing','on_the_way','delivered','canceled') NOT NULL,
  `new_status` ENUM('pending','accepted','preparing','on_the_way','delivered','canceled') NOT NULL,
  `changed_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `changed_by_user_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`history_id`),
  KEY `idx_statushistory_order` (`order_id`),
  KEY `idx_statushistory_user` (`changed_by_user_id`),
  CONSTRAINT `fk_statushistory_order` FOREIGN KEY (`order_id`) REFERENCES `Order`(`order_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_statushistory_user` FOREIGN KEY (`changed_by_user_id`) REFERENCES `User`(`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `ProductPriceHistory` (
  `price_history_id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `product_id` INT UNSIGNED NOT NULL,
  `old_price` DECIMAL(10,2) NOT NULL,
  `new_price` DECIMAL(10,2) NOT NULL,
  `changed_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `changed_by_user_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`price_history_id`),
  KEY `idx_pricehistory_product` (`product_id`),
  KEY `idx_pricehistory_user` (`changed_by_user_id`),
  CONSTRAINT `fk_pricehistory_product` FOREIGN KEY (`product_id`) REFERENCES `Product`(`product_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_pricehistory_user` FOREIGN KEY (`changed_by_user_id`) REFERENCES `User`(`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
