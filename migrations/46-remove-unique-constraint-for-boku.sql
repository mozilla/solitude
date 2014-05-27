ALTER TABLE `seller_product_boku`
    DROP FOREIGN KEY `seller_boku_id_refs_id_boku`,
    DROP INDEX `seller_boku_id`;
ALTER TABLE `seller_product_boku`
    ADD INDEX `seller_boku_id` (`seller_boku_id`),
    ADD CONSTRAINT `seller_boku_id_refs_id_boku` FOREIGN KEY (`seller_boku_id`) REFERENCES `seller_boku` (`id`);
