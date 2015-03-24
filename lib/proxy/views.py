import urllib
import urlparse

from django import http
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse

import requests
from django_statsd.clients import statsd
from lxml import etree
from slumber import url_join

from curling.lib import sign_request
from lib.bango.constants import HEADERS_SERVICE_GET, HEADERS_ALLOWED_INVERTED
from lib.boku.client import get_boku_request_signature
from lib.proxy.constants import HEADERS_URL_GET
from solitude.base import dump_request, dump_response
from solitude.logger import getLogger

log = getLogger('s.proxy')
bango_timeout = getattr(settings, 'BANGO_TIMEOUT', 10)


def qs_join(**kwargs):
    return '{url}?{query}'.format(**kwargs)


class Proxy(object):
    # Override this in your proxy class.
    name = None
    # Values that we'll populate from the request, optionally.
    body = None
    headers = None
    url = None
    # Name of settings variables.
    setting_proxy = 'SOLITUDE_PROXY'
    setting_timeout = ''
    # Nice name for the URL we are going to hit.
    service = ''

    def __init__(self):
        self.enabled = getattr(settings, self.setting_proxy, False)
        self.timeout = getattr(settings, self.setting_timeout, 10)

    def pre(self, request):
        """Do any processing of the incoming request."""
        self.method = request.META['REQUEST_METHOD'].lower()
        self.body = str(request.body)
        try:
            self.service = request.META[HEADERS_URL_GET]
        except KeyError:
            log.error('Missing header: %s',
                      ', '.join(sorted(request.META.keys())))
            raise

    def call(self):
        """Call the proxied service, return a response."""
        response = http.HttpResponse()
        method = getattr(requests, self.method)
        try:
            with statsd.timer('solitude.proxy.%s.%s' %
                              (self.service, self.name)):
                log.info('Calling service: %s at %s with %s' %
                         (self.service, self.url, self.method))
                dump_request(request=None, method=self.method, url=self.url,
                             body=self.body, headers=self.headers)
                # We aren't calling client._call because that tries to parse
                # the output. Once the headers are prepared, this will do the
                # rest.
                result = method(self.url, data=self.body,
                                headers=self.headers,
                                timeout=self.timeout, verify=True)
        except requests.exceptions.RequestException as err:
            dump_response(status_code=500)
            log.exception('%s: %s' % (err.__class__.__name__, err))
            response.status_code = 500
            return response

        dump_response(response=result)
        if result.status_code < 200 or result.status_code > 299:
            log.error('Warning response status: {0}'
                      .format(result.status_code))

        # Ensure the response passed along is updated with the response given.
        response.status_code = result.status_code
        response.content = result.text
        response['Content-Type'] = result.headers['Content-Type']
        return response

    def __call__(self, request):
        """Takes the incoming request and returns a response."""
        if not self.enabled:
            return http.HttpResponseNotFound()

        self.pre(request)
        response = self.call()
        response = self.post(response)
        return response

    def post(self, response):
        """Any post processing of the response here. Return the response."""
        return response


class BangoProxy(Proxy):
    name = 'bango'
    namespaces = ['com.bango.webservices.billingconfiguration',
                  'com.bango.webservices.directbilling',
                  'com.bango.webservices.mozillaexporter']
    setting_timeout = 'BANGO_TIMEOUT'
    service = 'bango'

    def __init__(self):
        self.enabled = getattr(settings, 'SOLITUDE_PROXY', False)
        self.timeout = getattr(settings, 'BANGO_TIMEOUT', 10)

    def tags(self, name):
        return ['{%s}%s' % (n, name) for n in self.namespaces]

    def pre(self, request):
        self.url = request.META[HEADERS_SERVICE_GET]
        self.headers = {'Content-Type': 'text/xml; charset=utf-8'}

        # Add in any headers we need to pass through,
        for k, v in HEADERS_ALLOWED_INVERTED.items():
            # Transform the key from the settings into the appropriate
            # format from Django request.
            k = 'HTTP_' + k.upper().replace('-', '_')
            if k in request.META:
                self.headers[v] = request.META[k]
                log.info('Adding header: {0}, {1}'.format(v, request.META[k]))

        # All the Bango methods are a POST.
        self.method = 'post'

        # Alter the XML to include the username and password from the config.
        # Perhaps this can be done quicker with XPath.
        root = etree.fromstring(request.body)
        username = self.tags('username')
        password = self.tags('password')
        changed_username = False
        changed_password = False
        for element in root.iter():
            if element.tag in username:
                element.text = settings.BANGO_AUTH.get('USER', '')
                changed_username = True
            elif element.tag in password:
                element.text = settings.BANGO_AUTH.get('PASSWORD', '')
                changed_password = True
            if changed_username and changed_password:
                break

        if not changed_username and not changed_password:
            log.info('Did not set a username and password on the request.')

        self.body = etree.tostring(root)


class ProviderProxy(Proxy):
    name = 'provider'

    def __init__(self, reference_name):
        self.reference_name = reference_name
        super(ProviderProxy, self).__init__()

        self.config = settings.ZIPPY_CONFIGURATION.get(self.reference_name)
        if not self.config:
            raise ImproperlyConfigured('No config: %s' % self.reference_name)

    def pre(self, request):
        # Headers we want from the proxying request.
        self.headers = {
            'Content-Type': request.META.get('CONTENT_TYPE'),
            'Accept': request.META.get('HTTP_ACCEPT')
        }
        self.body = str(request.body)
        self.method = request.META['REQUEST_METHOD'].lower()
        # The URL is made up of the defined scheme and host plus the trailing
        # URL after the proxy in urls.py.
        root = len(reverse('provider.proxy',
                   kwargs={'reference_name': self.reference_name}))

        self.url = url_join(self.config['url'],
                            request.META['PATH_INFO'][root:])
        # Add in the query string.
        query = request.META.get('QUERY_STRING')
        if query:
            self.url = qs_join(url=self.url, query=query)
        # Before we do the request, use curling to sign the request headers.
        log.info('%s: %s' % (self.method.upper(), self.url))
        self.sign(request)

    def sign(self, request):
        sign_request(None, self.config['auth'], headers=self.headers,
                     method=self.method.upper(),
                     params={'oauth_token': 'not-implemented'},
                     url=self.url)


class BokuProxy(ProviderProxy):
    name = 'boku'

    def sign(self, request):
        qs = request.META.get('QUERY_STRING')
        # The API request will come in with an invalid signature, lets
        # strip that out before resigning.
        qs = dict((k, v[0]) for k, v in urlparse.parse_qs(qs).items())
        qs['merchant-id'] = settings.BOKU_MERCHANT_ID
        # Sign the request.
        qs['sig'] = get_boku_request_signature(settings.BOKU_SECRET_KEY, qs)

        # Now put the URL back together, along with the query string.
        self.url = qs_join(url=self.url.split('?')[0],
                           query=urllib.urlencode(qs))


def check_sig(request):
    """
    Override the check_sig call, Boku doesn't actually implement this,
    the proxy does because it has access to that data. Rather than
    send the data on, or try overriding the client, just grab this request,
    parse it and send back a 204 or 400.
    """
    data = request.GET.copy()
    external_sig = data.pop('sig')[0]
    calculated_sig = get_boku_request_signature(settings.BOKU_SECRET_KEY, data)
    is_valid = external_sig == calculated_sig

    log.info('Boku check_sig: {0}'.format('PASS' if is_valid else 'FAIL'))
    return http.HttpResponse(status=204 if is_valid else 400)


def provider(request, reference_name):
    if reference_name == 'boku':
        return BokuProxy(reference_name)(request)
    return ProviderProxy(reference_name)(request)


def bango(request):
    return BangoProxy()(request)
