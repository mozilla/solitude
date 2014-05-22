ALTER TABLE `transaction` ADD COLUMN `seller_id` int(11) unsigned NULL;
ALTER TABLE `transaction` ADD CONSTRAINT `seller_id_refs_id_seller`
        FOREIGN KEY (`seller_id`) REFERENCES `seller` (`id`);
