CREATE TABLE `seller_bango` (
    `id` int(11) unsigned AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    `seller_id` int(11) unsigned NOT NULL UNIQUE,
    `package_id` int(11) NOT NULL UNIQUE,
    `admin_person_id` int(11) NOT NULL,
    `support_person_id` int(11) NOT NULL,
    `finance_person_id` int(11) NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

ALTER TABLE `seller_bango` ADD CONSTRAINT `seller_id_refs_id_c6c7badb`
    FOREIGN KEY (`seller_id`) REFERENCES `seller` (`id`);
