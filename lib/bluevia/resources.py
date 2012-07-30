from django.core.urlresolvers import reverse

from solitude.base import Cached, Resource as BaseResource

from .client import get_client
from .forms import PayValidation


class Null(object):
    pass


class Resource(BaseResource):

    class Meta(BaseResource.Meta):
        object_class = Cached

    def get_resource_uri(self, bundle):
        return reverse('api_dispatch_detail',
                        kwargs={'api_name': 'bluevia',
                                'resource_name': self._meta.resource_name,
                                'pk': bundle.obj.pk})


class PayResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'prepare-pay'
        list_allowed_methods = ['post']

    def obj_create(self, bundle, request, **kwargs):
        bluevia = get_client()
        form = PayValidation(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)
        bundle.data = {'jwt': bluevia.create_jwt(**form.cleaned_data)}
        return bundle
