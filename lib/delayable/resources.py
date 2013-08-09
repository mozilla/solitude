from django.conf.urls.defaults import url

from tastypie import http
from tastypie.exceptions import ImmediateHttpResponse

from lib.delayable.models import Delayable
from solitude.base import ModelResource


class BaseMixin(object):

    def base_urls(self):
        # Have url, based on uuid, not pk.
        return [
            url(r'^(?P<resource_name>%s)/(?P<uuid>[\w\d-]+)/$' %
                self._meta.resource_name, self.wrap_view('dispatch_detail'),
                name='api_dispatch_detail'),
        ]


class DelayableResource(BaseMixin, ModelResource):
    """This is a resource that points to the raw resource results."""

    class Meta(ModelResource.Meta):
        queryset = Delayable.objects.filter().order_by('-id')
        list_allowed_methods = ['get']
        allowed_methods = ['get']
        resource_name = 'result'
        filtering = {
            'uuid': 'exact'
        }


class ReplayResource(BaseMixin, ModelResource):
    """This is a resource that replay the result as another response."""

    class Meta(ModelResource.Meta):
        allowed_methods = ['get']
        resource_name = 'replay'

    def obj_get(self, request, **kwargs):
        # This is kinda weird and we don't really need to go through the entire
        # object dehydrate cycle, but just fake out our response.
        try:
            obj = Delayable.objects.get(**kwargs)
        except Delayable.DoesNotExist:
            raise ImmediateHttpResponse(response=http.HttpNotFound())

        response = http.HttpResponse(obj.content,
                                     content_type='application/json')
        response['Solitude-Async'] = 'yes' if obj.run else 'no'
        response.status_code = obj.status_code
        raise ImmediateHttpResponse(response=response)
