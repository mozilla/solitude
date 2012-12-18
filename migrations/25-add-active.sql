ALTER TABLE `buyer` ADD COLUMN `active` bool NOT NULL DEFAULT True;
CREATE INDEX `buyer_active` ON `buyer` (`active`);
ALTER TABLE `seller` ADD COLUMN `active` bool NOT NULL DEFAULT True;
CREATE INDEX `seller_active` ON `buyer` (`active`);
