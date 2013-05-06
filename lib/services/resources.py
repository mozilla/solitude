import json
import logging

from django.conf import settings
from django.core.cache import cache
from django.db import DatabaseError

from tastypie import http
from tastypie.exceptions import ImmediateHttpResponse
from tastypie_services.services import StatusError, StatusObject as Base

from lib.sellers.models import Seller
from solitude.base import Resource

log = logging.getLogger('s.services')


class StatusObject(Base):

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

    def test(self):
        self.test_cache()
        self.test_db()
        self.test_settings()

        if self.is_proxy:
            if self.settings and not (self.db and self.cache):
                return self
            raise StatusError(str(self))

        if self.db and self.cache:
            return self
        raise StatusError(str(self))


class RequestResource(Resource):
    """
    This is a resource that does nothing, just returns some information
    about the request. Useful for testing that solitude is working for you.
    """

    class Meta(Resource.Meta):
        list_allowed_methods = ['get']
        resource_name = 'request'

    def obj_get_list(self, request, **kwargs):
        content = {'authenticated': request.OAUTH_KEY}
        response = http.HttpResponse(content=json.dumps(content))
        raise ImmediateHttpResponse(response=response)
