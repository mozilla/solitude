from django.core.urlresolvers import reverse

from solitude.base import Cached, Resource as BaseResource
from ..client import get_client, response_to_dict
from ..errors import BangoFormError
from ..signals import create


class Form:
    """A fake form to pass through to form_errors"""

    def __init__(self, errors):
        self.errors = errors


class BangoResource(object):
    """A mixin that requires BaseResource to handle Bango form errors."""

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
        """
        Define error_lookup as a dictionary on a resource. If the error from
        Bango maps to a form field we'll put the error on that form field.
        Otherwise it gets assigned to __all__.
        """
        key = getattr(self, 'error_lookup', {}).get(exc.id, '__all__')
        return Form({key: [exc.message], '__bango__': exc.id,
                     '__type__': 'bango'})


class Resource(BaseResource, BangoResource):

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

    def obj_create(self, bundle, request, raise_on=None, **kwargs):
        self.check_meta()

        form = self._meta.simple_form(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        resp = self.client(self._meta.simple_api, form.bango_data,
                           raise_on=raise_on)
        create.send(sender=self, bundle=bundle,
                    data=response_to_dict(resp), form=form)
        return bundle
