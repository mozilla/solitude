BEGIN;
CREATE TABLE `seller` (
    `id` int(11) unsigned AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `uuid` varchar(255) NOT NULL UNIQUE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

CREATE TABLE `seller_paypal` (
    `id` int(11) unsigned AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `paypal_id` varchar(255),
    `token` varchar(255),
    `secret` varchar(255),
    `seller_id` int(11) unsigned NOT NULL UNIQUE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

ALTER TABLE `seller_paypal` ADD CONSTRAINT `seller_id_refs_id_829de2a6`
        FOREIGN KEY (`seller_id`) REFERENCES `seller` (`id`);
COMMIT;
