BEGIN;
CREATE TABLE `paypal_transaction` (
    `id` int(11) UNSIGNED AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `uuid` varchar(255) NOT NULL,
    `amount` numeric(9, 2) NOT NULL,
    `currency` varchar(3) NOT NULL,
    `pay_key` varchar(255) NOT NULL,
    `correlation_id` varchar(255) NOT NULL,
    `type` int(11) UNSIGNED NOT NULL,
    `status` int(11) UNSIGNED NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

CREATE INDEX `paypal_transaction_2bbc74ae` ON `paypal_transaction` (`uuid`);
CREATE INDEX `paypal_transaction_278d2c0e` ON `paypal_transaction` (`pay_key`);
CREATE INDEX `paypal_transaction_6fa770c7` ON `paypal_transaction` (`correlation_id`);
COMMIT;
