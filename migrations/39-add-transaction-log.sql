CREATE TABLE `transaction_log` (
    `id` int(11) unsigned AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    `counter` bigint,
    `transaction_id` integer NOT NULL,
    `type` int(11) unsigned NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

ALTER TABLE `transaction_log` ADD CONSTRAINT `transaction_id_id` FOREIGN KEY (`transaction_id`) REFERENCES `transaction` (`id`);
