ALTER TABLE `buyer` ADD COLUMN `new_pin` varchar(255);
ALTER TABLE `buyer` ADD COLUMN `needs_pin_reset` boolean NOT NULL DEFAULT 0;
