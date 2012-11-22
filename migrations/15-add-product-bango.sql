ALTER TABLE seller_product MODIFY id int(11) unsigned;

CREATE TABLE `sellers_sellerproductbango` (
    `id` int(11) unsigned AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    `seller_product_id` int(11) unsigned NOT NULL UNIQUE,
    `bango_id` varchar(128) NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

ALTER TABLE `sellers_sellerproductbango` ADD CONSTRAINT `seller_product_id_refs_id_bango`
        FOREIGN KEY (`seller_product_id`) REFERENCES `seller_product` (`id`);
