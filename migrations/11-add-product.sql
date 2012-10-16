CREATE TABLE `seller_product` (
    `id` int(11) AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    `seller_id` int(11) NOT NULL,
    `bango_secret` longtext
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

ALTER TABLE `seller_product` ADD CONSTRAINT `seller_id_refs_id_product`
        FOREIGN KEY (`seller_id`) REFERENCES `seller` (`id`);
CREATE INDEX `seller_product` ON `seller_product` (`seller_id`);
