CREATE TABLE `braintree_subscription` (
    `id` int(11) unsigned AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    `counter` bigint,
    `active` bool NOT NULL,
    `paymethod_id` int(11) unsigned NOT NULL,
    `seller_product_id` int(11) unsigned NOT NULL,
    `provider_id` varchar(255) NOT NULL,
    UNIQUE (`paymethod_id`, `seller_product_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
ALTER TABLE `braintree_subscription` ADD CONSTRAINT `seller_product_id_refs_id_b5dd89a4` FOREIGN KEY (`seller_product_id`) REFERENCES `seller_product` (`id`);
ALTER TABLE `braintree_subscription` ADD CONSTRAINT `paymethod_id_refs_id_1812d9f7` FOREIGN KEY (`paymethod_id`) REFERENCES `braintree_pay_method` (`id`);
CREATE INDEX `braintree_subscription_2bb89b7c` ON `braintree_subscription` (`paymethod_id`);
CREATE INDEX `braintree_subscription_d18be639` ON `braintree_subscription` (`seller_product_id`);
