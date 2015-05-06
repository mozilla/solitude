CREATE TABLE `braintree_pay_method` (
    `id` int(11) unsigned AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    `counter` bigint,
    `active` bool NOT NULL,
    `braintree_buyer_id` int(11) UNSIGNED NOT NULL,
    `provider_id` varchar(255) NOT NULL,
    `type` integer UNSIGNED NOT NULL,
    `type_name` varchar(255) NOT NULL,
    `truncated_id` varchar(255) NOT NULL
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
ALTER TABLE `braintree_pay_method` ADD CONSTRAINT `braintree_buyer_id_refs_id_f404a9d7` FOREIGN KEY (`braintree_buyer_id`) REFERENCES `buyer_braintree` (`id`);
CREATE INDEX `braintree_pay_method_ab6bc121` ON `braintree_pay_method` (`braintree_buyer_id`);
