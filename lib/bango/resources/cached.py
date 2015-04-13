from django.core.urlresolvers import reverse

from ..client import format_client_error, get_client
from ..errors import BangoFormError
from solitude.base import Cached, Resource as TastypieBaseResource


class BangoResource(object):

    def client(self, method, data, raise_on=None, client=None):
        """
        Client to call the bango client and process errors in a way that
        is relevant to the form. If you pass in a list of errors, these will
        be treated as errors the callee is going to deal with and will not
        be returning ImmediateHttpResponses. Instead the callee will have to
        cope with these BangoFormErrors as appropriate.

        You can optionally pass in a client to override the default.
        """
        raise_on = raise_on or []
        try:
            return getattr(client or get_client(), method)(data)
        except BangoFormError, exc:
            if exc.id in raise_on:
                raise

            res = self.handle_form_error(exc)
            return self.form_errors(res)

    def handle_form_error(self, exc):
        key = getattr(self, 'error_lookup', {}).get(exc.id, '__all__')
        return format_client_error(key, exc)


class Resource(TastypieBaseResource, BangoResource):

    class Meta(TastypieBaseResource.Meta):
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

    def obj_create(self, bundle, request, raise_on=None, **kwargs):
        self.check_meta()

        form = self._meta.simple_form(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        self.client(self._meta.simple_api, form.bango_data,
                    raise_on=raise_on)
        return bundle
