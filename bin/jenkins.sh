#!/bin/sh
# This script makes sure that Jenkins can properly run your tests against your
# codebase.

if [ -f /opt/rh/python27/enable ]; then
  source /opt/rh/python27/enable
fi

set -e


DB_HOST="localhost"
DB_USER="hudson"

cd $WORKSPACE
VENV=$WORKSPACE/venv

echo "Starting build on executor $EXECUTOR_NUMBER..."

# Make sure there's no old pyc files around.
find . -name '*.pyc' -exec rm {} \;

if [ ! -d "$VENV/bin" ]; then
  echo "No virtualenv found.  Making one..."
  virtualenv $VENV --system-site-packages --python=python
  source $VENV/bin/activate
  pip install --upgrade pip
fi

git submodule sync -q
git submodule update --init --recursive

source $VENV/bin/activate
pip install -q --exists-action=w --no-deps -r requirements/test.txt --no-index -f https://pyrepo.addons.mozilla.org/

cat > solitude/settings/local.py <<SETTINGS
from solitude.settings.base import *

DEBUG = True
SECRET_KEY = 'not-blank-honest'
ROOT_URLCONF = 'solitude.urls'
LOG_LEVEL = logging.ERROR
# Database name has to be set because of sphinx
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '${DB_HOST}',
        'NAME': '${JOB_NAME}',
        'USER': 'hudson',
        'PASSWORD': '',
        'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
        'TEST_NAME': 'test_${JOB_NAME}',
        'TEST_CHARSET': 'utf8',
        'TEST_COLLATION': 'utf8_general_ci',
    }
}

HMAC_KEYS = {  # for bcrypt only
    '2011-01-01': 'cheesecake',
}
from django_sha2 import get_password_hashers
PASSWORD_HASHERS = get_password_hashers(BASE_PASSWORD_HASHERS, HMAC_KEYS)

INSTALLED_APPS += ('django_nose',)
CELERY_ALWAYS_EAGER = True
SETTINGS

echo "Creating database if we need it..."
echo "CREATE DATABASE IF NOT EXISTS ${JOB_NAME}"|mysql -u $DB_USER -h $DB_HOST

echo "Starting tests..."
export FORCE_DB=1
python manage.py test --noinput --with-xunit --with-blockage

echo "FIN"
