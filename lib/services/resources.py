from solitude.base import Resource

from django.core.urlresolvers import reverse
from django.views import debug

from tastypie import fields
from tastypie import http
from tastypie.exceptions import ImmediateHttpResponse


class TestError(Exception):
    pass


class ErrorResource(Resource):

    class Meta(Resource.Meta):
        list_allowed_methods = ['get']
        resource_name = 'error'

    def obj_get_list(self, request=None, **kwargs):
        # All this does is throw an error. This is used for testing
        # the error handling on dev servers.
        raise TestError


class SettingsObject(object):

    def __init__(self, name):
        self.pk = name
        cleansed = debug.get_safe_settings()
        self.cleansed = debug.cleanse_setting(name, cleansed[name])


class SettingsResource(Resource):
    value = fields.CharField(readonly=True, attribute='cleansed')

    class Meta(Resource.Meta):
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
