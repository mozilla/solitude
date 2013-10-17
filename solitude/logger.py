import logging

from django.conf import settings

from solitude.middleware import get_oauth_key, get_transaction_id


def getLogger(name=None):
    logger = logging.getLogger(name)
    return SolitudeAdapter(logger)


# This really should be fulfilled by a logging filter which would remove the
# need to do all this crap. However I've got no idea how to do that and I
# wasted far too long on this.
class SolitudeAdapter(logging.LoggerAdapter):
    """Adds OAuth user and transaction id to every logging message's kwargs."""

    def __init__(self, logger, extra=None):
        logging.LoggerAdapter.__init__(self, logger, extra or {})

    def process(self, msg, kwargs):
        kwargs['extra'] = {'OAUTH_KEY': get_oauth_key(),
                           'TRANSACTION_ID': get_transaction_id()}
        return msg, kwargs


class SolitudeFormatter(logging.Formatter):

    def format(self, record):
        if not self._fmt.startswith(settings.SYSLOG_TAG):
            self._fmt = '%s %s' % (settings.SYSLOG_TAG, self._fmt)
        for name in 'OAUTH_KEY', 'TRANSACTION_ID':
            record.__dict__.setdefault(name, '')
        return logging.Formatter.format(self, record)
