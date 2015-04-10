import logging
import traceback
import urlparse

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.views import debug

import requests
from aesfield.field import AESField
from rest_framework.decorators import api_view
from rest_framework.response import Response

from lib.bango.constants import STATUS_BAD
from lib.sellers.models import Seller, SellerProduct
from lib.transactions.constants import STATUS_FAILED
from solitude.logger import getLogger

log = getLogger('s.services')


class StatusObject(object):

    def __init__(self):
        self.status = {}
        self.error = None

    @property
    def is_proxy(self):
        return getattr(settings, 'SOLITUDE_PROXY', {})

    def test_cache(self):
        # caching fails silently so we have to read from it after writing.
        cache.set('status', 'works')
        if cache.get('status') == 'works':
            return True

        return False

    def test_db(self):
        try:
            # exists is one of the fastest queries one can run.
            Seller.objects.exists()
            return True
        except Exception:
            log.info('Error connection to the db', exc_info=True)
            return False

    def test_settings(self):
        # Warn if the settings are confused and the proxy settings are
        # mixed with non-proxy settings. At this time we can't tell if you
        # are running just the database server or solitude all in one.
        self.status['settings'] = True
        caches = getattr(settings, 'CACHES', {})
        dbs = getattr(settings, 'DATABASES', {})

        if self.is_proxy:
            # As a proxy, we should not have database access.
            for db in dbs.values():
                engine = db.get('ENGINE', '')
                if (engine not in ['', 'django.db.backends.dummy']):
                    log.error('Proxy db set to: %s' % engine)
                    return False

            # There could be an issue if you share a proxy with the database
            # server, a local cache should be fine.
            for cache_ in caches.values():
                backend = cache_.get('BACKEND', '')
                valid = [
                    '',
                    'django.core.cache.backends.dummy.DummyCache',
                    'django.core.cache.backends.locmem.LocMemCache'
                ]
                if backend not in valid:
                    log.error('Proxy cache set to: %s' % backend)
                    return False

        else:
            # Tuck the encrypt test into settings.
            test = AESField(aes_key='bango:signature')
            if test._decrypt(test._encrypt('foo')) != 'foo':
                return False

        return True

    def test_proxies(self):
        self.status['proxies'] = True
        if not self.is_proxy and settings.BANGO_PROXY:
            # Ensure that we can speak to the proxy.
            home = urlparse.urlparse(settings.BANGO_PROXY)
            proxy = '%s://%s' % (home.scheme, home.netloc)
            try:
                requests.get(proxy, verify=True, timeout=5)
            except:
                log.error('Proxy error: %s' % proxy, exc_info=True)
                return False

        if self.is_proxy:
            # Ensure that we can speak to Bango.
            url = 'https://webservices.bango.com/billingconfiguration/?wsdl'
            try:
                requests.get(url, verify=True, timeout=30)
            except:
                log.error('Bango error: %s' % url, exc_info=True)
                return False

        return True


class TestError(Exception):
    pass


@api_view(['GET'])
def error(request):
    raise TestError('This is a test.')


@api_view(['GET'])
def logs(request):
    # Log palooza. Try logging to every log at every level.
    handlers = {'passed': [], 'failed': [], 'skipped': []}
    for log_name, log_obj in logging.root.manager.loggerDict.items():
        if isinstance(log_obj, logging.PlaceHolder):
            handlers['skipped'].append(log_name)
            continue

        for level_name in ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']:
            try:
                log_obj.log(
                    getattr(logging, level_name),
                    'Log at level: {0} to log: {1}.'
                    .format(level_name, log_name)
                )
                handlers['passed'].append([log_name, level_name])
            except:
                handlers['failed'].append([log_name, level_name,
                                           traceback.format_exc()])

    return Response(handlers)


@api_view(['GET'])
def status(request):
    obj = StatusObject()
    for key, method in (('proxies', obj.test_proxies),
                        ('db', obj.test_db),
                        ('cache', obj.test_cache),
                        ('settings', obj.test_settings)):
        obj.status[key] = method()

    if obj.is_proxy:
        if (obj.status['settings'] and not
                (obj.status['db'] and obj.status['cache'])):
            code = 200
        else:
            # The proxy should have good settings but not the db or cache.
            code = 500
    elif obj.status['db'] and obj.status['cache']:
        code = 200
    else:
        # The db instance should have a good db and cache.
        code = 500
    return Response(obj.status, status=code)


@api_view(['GET'])
def request_resource(request):
    return Response({'authenticated': request.OAUTH_KEY})


@api_view(['GET'])
def settings_list(request):
    if not getattr(settings, 'CLEANSED_SETTINGS_ACCESS', False):
        raise PermissionDenied
    return Response(sorted(debug.get_safe_settings().keys()))


@api_view(['GET'])
def settings_view(request, setting):
    if not getattr(settings, 'CLEANSED_SETTINGS_ACCESS', False):
        raise PermissionDenied
    return Response({'key': setting,
                     'value': debug.get_safe_settings()[setting]})


@api_view(['GET'])
def transactions_failures(request):
    transactions = []
    for seller_product in SellerProduct.objects.filter(
            transaction__status=STATUS_FAILED):
        transaction = seller_product.transaction_set.latest('modified')
        transactions.append({
            'id': transaction.id,
            'uid_support': transaction.uid_support,
            'uid_pay': transaction.uid_pay,
            'uuid': transaction.uuid,
            'uri': reverse('generic:transaction-detail',
                           kwargs={'pk': transaction.id}),
            'product_id': seller_product.external_id,
        })
    return Response({'transactions': transactions})


@api_view(['GET'])
def statuses_failures(request):
    statuses = []
    for seller_product in SellerProduct.objects.filter(
            product__status__status=STATUS_BAD):
        status = seller_product.product.status.latest('modified')
        statuses.append({
            'id': status.id,
            'errors': status.errors,
            'product_id': seller_product.external_id,
        })
    return Response({'statuses': statuses})
