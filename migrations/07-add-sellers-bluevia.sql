CREATE TABLE `seller_bluevia` (
    `id` int(11) unsigned AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `bluevia_id` varchar(255),
    `seller_id` int(11) unsigned NOT NULL UNIQUE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
