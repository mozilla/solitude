ALTER TABLE seller_product_bango DROP COLUMN uuid;
DELETE FROM seller_product_bango;
DELETE FROM seller_product;
ALTER TABLE seller_product ADD COLUMN external_id varchar(255) NOT NULL;
ALTER TABLE seller_product ADD UNIQUE (`seller_id`, `external_id`);
CREATE INDEX `seller_product_d5e787` ON `seller_product` (`external_id`);
