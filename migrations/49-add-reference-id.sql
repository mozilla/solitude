ALTER TABLE `seller_product_reference` ADD COLUMN `reference_id` VARCHAR(255) NOT NULL;
ALTER TABLE `seller_reference` CHANGE `merchant_id` `reference_id` VARCHAR(255) NOT NULL;
