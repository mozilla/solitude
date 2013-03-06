import json

from django.conf import settings
from raven.processors import Processor


class JSONProcessor(Processor):
    """
    This is a sentry wrapper to process the JSON and remove anything from it
    that could be considered as leaking sensitive data. Sentry has some
    processor for doing this, but they don't work with JSON posted in the body.
    """
    def process(self, data, **kwargs):
        http = data.get('sentry.interfaces.Http', None)
        if not http:
            return data
        try:
            http['data'] = json.dumps(sanitise(json.loads(http['data'])))
        except ValueError:
            # At this point we've got invalid JSON so things likely went
            # horribly wrong.
            pass

        return data


def sanitise(data, keys=None):
    """Sanitises keys in a dictionary."""
    keys = keys or settings.SENSITIVE_DATA_KEYS

    def recurse(leaf):
        for k, v in leaf.iteritems():
            if isinstance(v, dict):
                recurse(v)
            if k in keys:
                leaf[k] = '*' * 8

    recurse(data)
    return data
