# Startup script for running Solitude under Docker.

# Check for mysql being up and running.
mysqladmin -u root --host mysql_1 --silent --wait=30 ping || exit 1

# Check database exists. If not create it first.
mysql -u root --host mysql_1 -e 'use solitude;'
if [ $? -ne 0 ]; then
    echo "Solitude database doesn't exist. Let's create it"
    mysql -u root --host mysql_1 -e 'create database solitude'
    echo "Since we didn't have a db. Lets run the migrations."
    schematic migrations/
fi

if [ "$BRAINTREE_MERCHANT_ID" ]; then
    echo "Braintree merchant ID found in environment, running braintree_config."
    python manage.py braintree_config
fi

python manage.py runserver 0.0.0.0:2602
