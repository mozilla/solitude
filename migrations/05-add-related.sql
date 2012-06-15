BEGIN;
ALTER TABLE `transaction_paypal` ADD COLUMN `related_id` int(11) unsigned;
ALTER TABLE `transaction_paypal` ADD CONSTRAINT `related_id_refs_id_d6e42cbd`
        FOREIGN KEY (`related_id`) REFERENCES `transaction_paypal` (`id`);
CREATE INDEX `transaction_paypal_cb822826` ON `transaction_paypal` (`related_id`);
COMMIT;
