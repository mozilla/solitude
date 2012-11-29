-- Do stuff I forgot to do first time.
ALTER TABLE transaction ENGINE = InnoDB AUTO_INCREMENT = 1
        DEFAULT CHARSET = utf8 COLLATE=utf8_unicode_ci;

-- Make these columns unique when combined with provider.
ALTER TABLE transaction DROP INDEX uid_pay;
ALTER TABLE transaction DROP INDEX uid_support;
ALTER TABLE transaction ADD INDEX (`uid_pay`, `provider`);
ALTER TABLE transaction ADD INDEX (`uid_support`, `provider`);

-- Make uid_support nullable;
ALTER TABLE transaction modify uid_support varchar(255);
