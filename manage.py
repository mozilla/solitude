#!/usr/bin/env python
import os
import sys

# Edit this if necessary or override the variable in your environment.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solitude.settings')
if len(sys.argv) > 1 and sys.argv[1] == 'test':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'solitude.settings.test'

# This constant moved in Django 1.5 but it is used by Tastypie. When that
# gets updated we can remove this.
from django.db.models.sql import constants
try:
    from django.db.models.constants import LOOKUP_SEP
    constants.LOOKUP_SEP = LOOKUP_SEP
except ImportError:
    pass

# Tastypie pulls in simplejson from Django if it can. But simplejson is now
# incompatible with the std lib json. So its removed from our requirements.
# However Jenkins has simplejson installed globally, meaning it gets pulled in
# and fails.
import json
try:
    from django import utils
    utils.simplejson = json
except ImportError:
    pass


# Specifically importing once the environment has been setup.
from django.conf import settings
newrelic_ini = getattr(settings, 'NEWRELIC_INI', None)

if newrelic_ini and os.path.exists(newrelic_ini):
    import newrelic.agent
    try:
        newrelic.agent.initialize(newrelic_ini)
    except newrelic.api.exceptions.ConfigurationError:
        import logging
        startup_logger = logging.getLogger('s.startup')
        startup_logger.exception('Failed to load new relic config.')

from solitude.utils import validate_settings
validate_settings()


# Alter solitude to run on a particular port as per the
# marketplace docs, unless overridden.
from django.core.management.commands import runserver
runserver.DEFAULT_PORT = 2602

if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
