DELETE FROM `transaction`;
ALTER TABLE `transaction` DROP FOREIGN KEY `seller_id_refs_id_seller`;
ALTER TABLE `transaction` DROP COLUMN `seller_id`;
ALTER TABLE `transaction` ADD COLUMN `seller_product_id` int(11) unsigned NOT NULL;
ALTER TABLE `transaction` ADD CONSTRAINT `seller_product_id_refs_id_product`
        FOREIGN KEY (`seller_product_id`) REFERENCES `seller_product` (`id`);
