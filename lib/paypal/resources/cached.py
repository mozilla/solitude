from django.core.urlresolvers import reverse


from lib.paypal.client import get_client
from lib.paypal.signals import create
from solitude.base import Cached, Resource as TastypieBaseResource


class Resource(TastypieBaseResource):

    class Meta(TastypieBaseResource.Meta):
        object_class = Cached

    def get_resource_uri(self, bundle):
        return reverse(
            'api_dispatch_detail',
            kwargs={
                'api_name': 'paypal',
                'resource_name': self._meta.resource_name,
                'pk': bundle.obj.pk
            })

    def obj(self, pk=None):
        return self._meta.object_class(prefix=self._meta.resource_name, pk=pk)

    def obj_create(self, bundle, request, **kwargs):
        form = self._meta.form(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        paypal = get_client()
        bundle.data = getattr(paypal, self._meta.method)(*form.args())
        create.send(sender=self, bundle=bundle)
        return bundle
