CREATE TABLE `seller_boku` (
    `id` int(11) unsigned AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    `counter` bigint,
    `seller_id` int(11) unsigned NOT NULL UNIQUE,
    `merchant_id` varchar(255) NOT NULL,
    `service_id` varchar(255) NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

ALTER TABLE `seller_boku` ADD CONSTRAINT `seller_id_refs_id_d3a72381` FOREIGN KEY (`seller_id`) REFERENCES `seller` (`id`);
