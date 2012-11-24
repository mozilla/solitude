from django.core.urlresolvers import reverse

from solitude.base import Cached, Resource as BaseResource


class Resource(BaseResource):

    class Meta(BaseResource.Meta):
        object_class = Cached

    def get_resource_uri(self, bundle):
        return reverse('api_dispatch_detail',
                        kwargs={'api_name': 'bango',
                                'resource_name': self._meta.resource_name,
                                'pk': bundle.obj.pk})

    def obj(self, pk=None):
        return self._meta.object_class(prefix=self._meta.resource_name, pk=pk)
