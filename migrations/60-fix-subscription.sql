# This was accidentally changed in https://github.com/mozilla/solitude/pull/535
# This patch puts it back.
ALTER TABLE `braintree_transaction` CHANGE COLUMN `subscription` `subscription_id` int(11) unsigned;
