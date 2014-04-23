CREATE TABLE `seller_product_boku` (
    `id` int(11) unsigned AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    `counter` bigint,
    `seller_product_id` int(11) unsigned NOT NULL UNIQUE,
    `seller_boku_id` int(11) unsigned NOT NULL UNIQUE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

ALTER TABLE `seller_product_boku` ADD CONSTRAINT `seller_product_id_refs_id_boku`
    FOREIGN KEY (`seller_product_id`) REFERENCES `seller_product` (`id`);
ALTER TABLE `seller_product_boku` ADD CONSTRAINT `seller_boku_id_refs_id_boku`
    FOREIGN KEY (`seller_boku_id`) REFERENCES `seller_boku` (`id`);
