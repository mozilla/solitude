ALTER TABLE `seller_paypal`
    ADD COLUMN `first_name` varchar(255) NOT NULL,
    ADD COLUMN `last_name` varchar(255) NOT NULL,
    ADD COLUMN `full_name` varchar(255) NOT NULL,
    ADD COLUMN `business_name` varchar(255) NOT NULL,
    ADD COLUMN `country` varchar(64) NOT NULL,
    ADD COLUMN `address_one` varchar(255) NOT NULL,
    ADD COLUMN `address_two` varchar(255) NOT NULL,
    ADD COLUMN `post_code` varchar(128) NOT NULL,
    ADD COLUMN `city` varchar(128) NOT NULL,
    ADD COLUMN `state` varchar(64) NOT NULL,
    ADD COLUMN `phone` varchar(32) NOT NULL;
