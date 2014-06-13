CREATE TABLE `seller_reference` (
    `id` int(11) unsigned AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    `counter` bigint,
    `seller_id` int(11) unsigned NOT NULL UNIQUE,
    `merchant_id` varchar(255) NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

ALTER TABLE `seller_reference` ADD CONSTRAINT `seller_id_refs_id_d3a72381` FOREIGN KEY (`seller_id`) REFERENCES `seller` (`id`);

CREATE TABLE `seller_product_reference` (
    `id` int(11) unsigned AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    `counter` bigint,
    `seller_product_id` int(11) unsigned NOT NULL UNIQUE,
    `seller_reference_id` int(11) unsigned NOT NULL UNIQUE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

ALTER TABLE `seller_product_reference` ADD CONSTRAINT `seller_product_id_refs_id_reference`
    FOREIGN KEY (`seller_product_id`) REFERENCES `seller_product` (`id`);
ALTER TABLE `seller_product_reference` ADD CONSTRAINT `seller_reference_id_refs_id_reference`
    FOREIGN KEY (`seller_reference_id`) REFERENCES `seller_reference` (`id`);
