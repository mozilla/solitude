import json
import logging

import requests

log = logging.getLogger('s.client')


class SolitudeError(Exception):
    pass


class Solitude(object):

    def __init__(self, config=None):
        self.config = self.parse(config)

    def get_url(self, name, pk=None):
        url = '%s/1/%s/' % (self.config['server'], name)
        return '%s%s/' % (url, pk) if pk else url

    def parse(self, config=None):
        config = {
            'server': config.get('server')
            # TODO: add in OAuth stuff.
        }
        return config

    def call(self, url, method, data=None):
        data = json.dumps(data) if data else None
        method = getattr(requests, method)

        result = method(url, data=data,
                        headers={'content-type': 'application/json'})

        if result.status_code in (200, 201):
            return json.loads(result.text)
        else:
            data = ''
            try:
                data = json.loads(result.text)
            except:
                log.error('Failed to parse error: %s' % result.text)
                pass
            raise SolitudeError(result.status_code, data)

    def add_buyer(self, uuid):
        return self.call(self.get_url('buyer'), 'post', {'uuid': uuid})
