ALTER TABLE buyer ADD COLUMN created datetime NOT NULL;
ALTER TABLE buyer ADD COLUMN modified datetime NOT NULL;

ALTER TABLE buyer_paypal ADD COLUMN created datetime NOT NULL;
ALTER TABLE buyer_paypal ADD COLUMN modified datetime NOT NULL;

ALTER TABLE seller ADD COLUMN created datetime NOT NULL;
ALTER TABLE seller ADD COLUMN modified datetime NOT NULL;

ALTER TABLE seller_paypal ADD COLUMN created datetime NOT NULL;
ALTER TABLE seller_paypal ADD COLUMN modified datetime NOT NULL;

ALTER TABLE seller_bluevia ADD COLUMN created datetime NOT NULL;
ALTER TABLE seller_bluevia ADD COLUMN modified datetime NOT NULL;

ALTER TABLE transaction_paypal ADD COLUMN created datetime NOT NULL;
ALTER TABLE transaction_paypal ADD COLUMN modified datetime NOT NULL;
