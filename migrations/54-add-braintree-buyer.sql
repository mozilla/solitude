CREATE TABLE `buyer_braintree` (
    `id` int(11) unsigned AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    `counter` bigint,
    `active` bool NOT NULL,
    `braintree_id` varchar(255) NOT NULL UNIQUE,
    `buyer_id` int(11) UNSIGNED NOT NULL UNIQUE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
ALTER TABLE `buyer_braintree` ADD CONSTRAINT `buyer_id` FOREIGN KEY (`buyer_id`) REFERENCES `buyer` (`id`);
