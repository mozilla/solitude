import logging
import urlparse

from django import http
from django.conf import settings

from django_statsd.clients import statsd
import requests

from lib.paypal.client import get_client
from lib.paypal.constants import HEADERS_URL, HEADERS_TOKEN
from lib.paypal.map import urls

log = logging.getLogger('s.proxy')
timeout = getattr(settings, 'PAYPAL_TIMEOUT', 10)


def proxy(request):
    if not settings.SOLITUDE_PROXY:
        return http.HttpResponseNotFound()

    data = request.raw_post_data
    try:
        service = request.META['HTTP_' + HEADERS_URL]
    except KeyError:
        log.error('Missing header: %s', ', '.join(sorted(request.META.keys())))
        raise

    token = request.META.get('HTTP_' + HEADERS_TOKEN)
    if token:
        token = dict(urlparse.parse_qsl(token))
    url = urls[service]

    client = get_client()
    headers = client.headers(url, auth_token=token)
    response = http.HttpResponse()

    try:
        with statsd.timer('solitude.proxy.paypal.%s' % service):
            log.info('Calling service: %s' % service)
            # We aren't calling client._call because that tries to parse the
            # output. Once the headers are prepared, this will do the rest.
            result = requests.post(url, data=data, headers=headers,
                                   timeout=timeout, verify=True)
    except requests.exceptions.RequestException as err:
        log.error(err.__class__.__name__)
        response.status_code = 500
        return response

    response.status_code = result.status_code
    response.content = result.text
    return response
