from lib.sellers.models import Seller
from solitude.base import ServiceResource

from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import DatabaseError
from django.views import debug

from tastypie import fields
from tastypie import http
from tastypie.exceptions import ImmediateHttpResponse


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

    def __repr__(self):
        return '<Status: database: %s, cache: %s>' % (self.db, self.cache)


class StatusResource(ServiceResource):
    cache = fields.BooleanField(readonly=True, attribute='cache')
    db = fields.BooleanField(readonly=True, attribute='db')

    class Meta(ServiceResource.Meta):
        list_allowed_methods = ['get']
        allowed_methods = ['get']
        resource_name = 'status'

    def obj_get(self, request, **kwargs):
        obj = StatusObject()
        # caching fails silently so we have to read from it after writing.
        cache.set('status', 'works')

        if cache.get('status') == 'works':
            obj.cache = True

        try:
            # exists is one of the fastest queries one can run.
            Seller.objects.exists()
            obj.db = True
        except DatabaseError:
            pass

        if all((obj.db, obj.cache)):
            return obj
        else:
            raise StatusError(str(obj))

    def obj_get_list(self, request=None, **kwargs):
        return [self.obj_get(request, **kwargs)]
