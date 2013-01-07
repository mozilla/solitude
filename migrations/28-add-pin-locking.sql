ALTER TABLE `buyer` ADD COLUMN `pin_failures` integer NOT NULL;
ALTER TABLE `buyer` ADD COLUMN `pin_locked_out` datetime;
