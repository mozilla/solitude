ALTER TABLE `braintree_transaction` CHANGE COLUMN `paymethod_id` `paymethod_id` int(11) unsigned;
ALTER TABLE `braintree_transaction` CHANGE COLUMN `subscription_id` `subscription` int(11) unsigned;
ALTER TABLE `braintree_transaction` CHANGE COLUMN `billing_period_end_date` `billing_period_end_date` datetime(6);
ALTER TABLE `braintree_transaction` CHANGE COLUMN `billing_period_start_date` `billing_period_start_date` datetime(6);
ALTER TABLE `braintree_transaction` CHANGE COLUMN `next_billing_date` `next_billing_date` datetime(6);
