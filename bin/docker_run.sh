# Startup script for running Solitude under Docker.

# Check database exists. If not create it first.
mysql -u root --host mysql_1 -e 'use solitude;'
if [ $? -ne 0 ]; then
    echo "Solitude database doesn't exist. Let's create it"
    mysql -u root --host mysql_1 -e 'create database solitude'
    echo "Since we didn't have a db. Lets run the migrations."
    schematic migrations/
fi

python manage.py runserver 0.0.0.0:2602
