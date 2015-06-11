CREATE TABLE `braintree_transaction` (
    `id` int(11) unsigned AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime(6) NOT NULL,
    `modified` datetime(6) NOT NULL,
    `counter` bigint,
    `transaction_id` int(11) unsigned NOT NULL UNIQUE,
    `paymethod_id` int(11) unsigned NOT NULL,
    `subscription_id` int(11) unsigned NOT NULL,
    `billing_period_end_date` datetime(6) NOT NULL,
    `billing_period_start_date` datetime(6) NOT NULL,
    `kind` varchar(255) NOT NULL,
    `next_billing_date` datetime(6) NOT NULL,
    `next_billing_period_amount` numeric(9, 2)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
ALTER TABLE `braintree_transaction` ADD CONSTRAINT `subscription_id_refs_id_76dfe860` FOREIGN KEY (`subscription_id`) REFERENCES `braintree_subscription` (`id`);
ALTER TABLE `braintree_transaction` ADD CONSTRAINT `paymethod_id_refs_id_e9b15dff` FOREIGN KEY (`paymethod_id`) REFERENCES `braintree_pay_method` (`id`);
ALTER TABLE `braintree_transaction` ADD CONSTRAINT `transaction_id_refs_id_35773a94` FOREIGN KEY (`transaction_id`) REFERENCES `transaction` (`id`);
CREATE INDEX `braintree_transaction_2bb89b7c` ON `braintree_transaction` (`paymethod_id`);
CREATE INDEX `braintree_transaction_b75baf19` ON `braintree_transaction` (`subscription_id`);
