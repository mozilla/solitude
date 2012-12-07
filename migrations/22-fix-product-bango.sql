# seller_bango is many-to-one and should not be unique.
ALTER TABLE seller_product_bango DROP FOREIGN KEY seller_bango_id_refs_id_bango;
ALTER TABLE seller_product_bango DROP INDEX seller_bango_id;
ALTER TABLE `seller_product_bango` ADD CONSTRAINT `seller_bango_id_refs_id_bango`
    FOREIGN KEY (`seller_bango_id`) REFERENCES `seller_bango` (`id`);
