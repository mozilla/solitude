DROP TABLE transaction_paypal;
CREATE TABLE `transaction` (
    `id` int(11) unsigned AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    `amount` numeric(9, 2) NOT NULL,
    `buyer_id` int(11) UNSIGNED,
    `currency` varchar(3) NOT NULL,
    `provider` int(11) UNSIGNED NOT NULL,
    `related_id` int(11) UNSIGNED ,
    `seller_id` int(11) UNSIGNED NOT NULL,
    `status` int(11) UNSIGNED NOT NULL,
    `source` varchar(255),
    `type` int(11) UNSIGNED NOT NULL,
    `uid_support` varchar(255) NOT NULL UNIQUE,
    `uid_pay` varchar(255) NOT NULL UNIQUE,
    `uuid` varchar(255) NOT NULL UNIQUE
)
;
ALTER TABLE `transaction` ADD CONSTRAINT `buyer_id_refs_id_buyer`
        FOREIGN KEY (`buyer_id`) REFERENCES `buyer` (`id`);
ALTER TABLE `transaction` ADD CONSTRAINT `seller_id_refs_id_seller`
        FOREIGN KEY (`seller_id`) REFERENCES `seller` (`id`);
ALTER TABLE `transaction` ADD CONSTRAINT `related_id_refs_id_transaction`
        FOREIGN KEY (`related_id`) REFERENCES `transaction` (`id`);
CREATE INDEX `transaction_buyer` ON `transaction` (`buyer_id`);
CREATE INDEX `transaction_related` ON `transaction` (`related_id`);
CREATE INDEX `transaction_seller` ON `transaction` (`seller_id`);
CREATE INDEX `transaction_source` ON `transaction` (`source`);
