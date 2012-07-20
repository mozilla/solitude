from cached import Resource

from lib.paypal.client import Client
from lib.paypal.forms import GetPersonal


class Personal(object):

    def obj_create(self, bundle, request, **kwargs):
        form = self._meta.form(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        paypal = Client()
        result = getattr(paypal, self._meta.method)(*form.args())
        for k, v in result.items():
            setattr(form.cleaned_data['seller'], k, v)
        form.cleaned_data['seller'].save()
        bundle.data = result
        bundle.obj = form.cleaned_data['seller']
        return bundle


class CheckPersonalBasic(Personal, Resource):

    class Meta(Resource.Meta):
        resource_name = 'personal-basic'
        list_allowed_methods = ['post']
        form = GetPersonal
        method = 'get_personal_basic'


class CheckPersonalAdvanced(Personal, Resource):

    class Meta(Resource.Meta):
        resource_name = 'personal-advanced'
        list_allowed_methods = ['post']
        form = GetPersonal
        method = 'get_personal_advanced'
