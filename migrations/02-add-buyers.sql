BEGIN;
CREATE TABLE `buyer` (
    `id` int(11) unsigned AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `uuid` varchar(255) UNIQUE NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

CREATE TABLE `buyer_paypal` (
    `id` int(11) unsigned AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `key` varchar(255),
    `expiry` date,
    `currency` varchar(3),
    `buyer_id` int(11) unsigned NOT NULL UNIQUE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

ALTER TABLE `buyer_paypal` ADD CONSTRAINT `buyer_id_refs_id_34d8ab16`
        FOREIGN KEY (`buyer_id`) REFERENCES `buyer` (`id`);
COMMIT;
