from cached import Resource

from lib.bango.client import get_client
from lib.bango.forms import CreateBankDetailsForm
from lib.bango.signals import create


class CreateBankDetailsResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'bank'
        list_allowed_methods = ['post']

    def obj_create(self, bundle, request, **kwargs):
        form = CreateBankDetailsForm(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        data = form.bango_data
        resp = get_client().CreateBankDetails(data)
        bundle.data = {'responseCode': resp.responseCode,
                       'responseMessage': resp.responseMessage}
        create.send(sender=self, bundle=bundle, data=data, form=form)
        return bundle
