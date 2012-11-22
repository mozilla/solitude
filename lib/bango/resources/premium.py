from cached import Resource

from lib.bango.client import get_client
from lib.bango.forms import MakePremiumForm


class MakePremiumResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'make-premium'
        list_allowed_methods = ['post']

    def obj_create(self, bundle, request, **kwargs):
        form = MakePremiumForm(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        get_client().MakePremiumPerAccess(form.bango_data)
        # It looks like we don't get a response to do anything with.
        return bundle
