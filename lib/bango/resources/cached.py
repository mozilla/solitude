from django.core.urlresolvers import reverse

from solitude.base import Cached, Resource as BaseResource
from ..client import get_client, response_to_dict
from ..signals import create


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


class SimpleResource(Resource):
    """
    A simple Bango base resource, for use with some of the simpler Bango APIs
    which just take data and pass it on as a POST and don't do much with the
    data. Use and override as neccessary.
    """

    class Meta(Resource.Meta):
        list_allowed_methods = ['post']
        simple_form = None  # Point to the form you'd like to use.
        simple_api = None  # This is the Bango API that will be called.

    def check_meta(self):
        # Just in case someone forgot to override.
        for k in ['simple_form', 'simple_api']:
            if not getattr(self._meta, k):
                raise ValueError('%s not set' % k)

    def obj_create(self, bundle, request, **kwargs):
        self.check_meta()

        form = self._meta.simple_form(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        resp = getattr(get_client(), self._meta.simple_api)(form.bango_data)
        create.send(sender=self, bundle=bundle,
                    data=response_to_dict(resp), form=form)
        return bundle
