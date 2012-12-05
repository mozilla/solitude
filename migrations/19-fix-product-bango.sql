DELETE FROM seller_product_bango;
ALTER TABLE seller_product_bango ADD COLUMN uuid varchar(255) NOT NULL UNIQUE;
