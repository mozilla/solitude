from lib.sellers.models import Seller
from solitude.base import ServiceResource

from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import DatabaseError
from django.views import debug

from tastypie import fields
from tastypie import http
from tastypie.exceptions import ImmediateHttpResponse

import logging

log = logging.getLogger('s.services')


class TestError(Exception):
    pass


class StatusError(Exception):
    pass


class ErrorResource(ServiceResource):

    class Meta(ServiceResource.Meta):
        list_allowed_methods = ['get']
        resource_name = 'error'

    def obj_get_list(self, request=None, **kwargs):
        # All this does is throw an error. This is used for testing
        # the error handling on dev servers.
        raise TestError('This is a test.')


class SettingsObject(object):

    def __init__(self, name):
        self.pk = name
        cleansed = debug.get_safe_settings()
        self.cleansed = debug.cleanse_setting(name, cleansed[name])


class SettingsResource(ServiceResource):
    value = fields.CharField(readonly=True, attribute='cleansed', null=True)
    key = fields.CharField(readonly=True, attribute='pk')

    class Meta(ServiceResource.Meta):
        list_allowed_methods = ['get']
        allowed_methods = ['get']
        resource_name = 'settings'

    def get_resource_uri(self, bundle):
        return reverse('api_dispatch_detail',
                        kwargs={'api_name': 'services',
                                'resource_name': 'settings',
                                'pk': bundle.obj.pk})

    def obj_get(self, request, **kwargs):
        pk = kwargs['pk']
        cleansed = debug.get_safe_settings()
        if pk not in cleansed:
            raise ImmediateHttpResponse(response=http.HttpNotFound())
        return SettingsObject(pk)

    def obj_get_list(self, request, **kwargs):
        keys = sorted(debug.get_safe_settings().keys())
        return [SettingsObject(k) for k in keys]


class StatusObject(object):
    pk = 'status'
    cache = False
    db = False
    settings = True

    def __repr__(self):
        values = ['%s: %s' % (k, v) for k, v in self.checks]
        return '<Status: %s>' % ', '.join(values)

    @property
    def checks(self):
        return [(k, getattr(self, k)) for k in ['cache', 'db', 'settings']]

    @property
    def is_proxy(self):
        return getattr(settings, 'SOLITUDE_PROXY', {})

    def test_cache(self):
        # caching fails silently so we have to read from it after writing.
        cache.set('status', 'works')

        if cache.get('status') == 'works':
            self.cache = True

    def test_db(self):
        try:
            # exists is one of the fastest queries one can run.
            Seller.objects.exists()
            self.db = True
        except DatabaseError:
            pass

    def test_settings(self):
        # Warn if the settings are confused and the proxy settings are
        # mixed with non-proxy settings. At this time we can't tell if you
        # are running just the database server or solitude all in one.
        caches = getattr(settings, 'CACHES', {})
        dbs = getattr(settings, 'DATABASES', {})

        if self.is_proxy:
            # As a proxy, we should not have database access.
            for db in dbs.values():
                engine = db.get('ENGINE', '')
                if (db.get('ENGINE', '') not in ['',
                        'django.db.backends.dummy']):
                    log.error('Proxy db set to: %s' % engine)
                    self.settings = False

            # There could be an issue if you share a proxy with the database
            # server, a local cache should be fine.
            for cache in caches.values():
                backend = cache.get('BACKEND', '')
                if (backend not in ['',
                        'django.core.cache.backends.dummy.DummyCache',
                        'django.core.cache.backends.locmem.LocMemCache']):
                    log.error('Proxy cache set to: %s' % backend)
                    self.settings = False


class StatusResource(ServiceResource):
    cache = fields.BooleanField(readonly=True, attribute='cache')
    db = fields.BooleanField(readonly=True, attribute='db')
    settings = fields.BooleanField(readonly=True, attribute='settings')

    class Meta(ServiceResource.Meta):
        list_allowed_methods = ['get']
        allowed_methods = ['get']
        resource_name = 'status'

    def obj_get(self, request, **kwargs):
        obj = StatusObject()
        obj.test_cache()
        obj.test_db()
        obj.test_settings()

        if obj.is_proxy:
            if obj.settings and not (obj.db and obj.cache):
                return obj
            raise StatusError(str(obj))

        if obj.db and obj.cache:
            return obj
        raise StatusError(str(obj))

    def obj_get_list(self, request=None, **kwargs):
        return [self.obj_get(request, **kwargs)]
