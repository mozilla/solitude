CREATE TABLE `delayable` (
    `id` int(11) unsigned AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    `uuid` varchar(36) NOT NULL,
    `run` bool NOT NULL,
    `status_code` int(11) unsigned NOT NULL,
    `content` longtext NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
