import uuid

from django.core.cache import cache
from django.core.urlresolvers import reverse

from tastypie import http
from tastypie.exceptions import ImmediateHttpResponse

from solitude.base import Resource as BaseResource


class Cached(object):
    def __init__(self, prefix='cached', pk=None):
        pk = pk if pk else uuid.uuid4()
        self.prefixed = '%s:%s' % (prefix, pk)
        self.pk = pk

    def set(self, data):
        return cache.set(self.prefixed, data)

    def get(self):
        return cache.get(self.prefixed)

    def get_or_404(self):
        res = self.get()
        if not res:
            raise ImmediateHttpResponse(response=http.HttpNotFound())
        return res

    def delete(self):
        cache.delete(self.prefixed)


class Resource(BaseResource):

    class Meta(BaseResource.Meta):
        object_class = Cached

    def get_resource_uri(self, bundle):
        return reverse('api_dispatch_detail',
                        kwargs={'api_name': 'paypal',
                                'resource_name': self._meta.resource_name,
                                'pk': bundle.obj.pk})

    def obj(self, pk=None):
        return self._meta.object_class(prefix=self._meta.resource_name, pk=pk)
