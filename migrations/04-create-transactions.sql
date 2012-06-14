BEGIN;
CREATE TABLE `transaction_paypal` (
    `id` int(11) UNSIGNED AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `uuid` varchar(255) NOT NULL,
    `seller_id` int(11) UNSIGNED NOT NULL,
    `amount` numeric(9, 2) NOT NULL,
    `currency` varchar(3) NOT NULL,
    `pay_key` varchar(255) NOT NULL,
    `correlation_id` varchar(255) NOT NULL,
    `type` int(11) UNSIGNED NOT NULL,
    `status` int(11) UNSIGNED NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

ALTER TABLE `transaction_paypal` ADD CONSTRAINT `seller_id_refs_id_8e346857`
        FOREIGN KEY (`seller_id`) REFERENCES `seller_paypal` (`id`);
CREATE INDEX `transaction_paypal_2bbc74ae` ON `transaction_paypal` (`uuid`);
CREATE INDEX `transaction_paypal_2ef613c9` ON `transaction_paypal` (`seller_id`);
CREATE INDEX `transaction_paypal_278d2c0e` ON `transaction_paypal` (`pay_key`);
CREATE INDEX `transaction_paypal_6fa770c7` ON `transaction_paypal` (`correlation_id`);
COMMIT;
