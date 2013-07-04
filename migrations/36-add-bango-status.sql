CREATE TABLE `status_bango` (
    `id` int(11) unsigned AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    `status` int(11) NOT NULL,
    `errors` longtext NOT NULL,
    `seller_product_bango_id` int(11) unsigned NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

ALTER TABLE `status_bango` ADD CONSTRAINT `seller_product_bango_id_refs_id_1c77c54e` FOREIGN KEY (`seller_product_bango_id`) REFERENCES `seller_product_bango` (`id`);
CREATE INDEX `status_bango_eae63669` ON `status_bango` (`seller_product_bango_id`);
