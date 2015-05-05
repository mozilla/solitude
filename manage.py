#!/usr/bin/env python
import os
import sys

# Edit this if necessary or override the variable in your environment.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solitude.settings')
if len(sys.argv) > 1 and sys.argv[1] == 'test':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'solitude.settings.test'


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
