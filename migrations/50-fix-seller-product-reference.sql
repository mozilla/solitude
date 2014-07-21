ALTER TABLE seller_product_reference DROP FOREIGN KEY seller_reference_id_refs_id_reference;
# Remove the unique index.
DROP INDEX seller_reference_id ON seller_product_reference;
ALTER TABLE `seller_product_reference` ADD CONSTRAINT `seller_reference_id_refs_id_reference`
    FOREIGN KEY (`seller_reference_id`) REFERENCES `seller_reference` (`id`);
