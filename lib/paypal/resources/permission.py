from cached import Resource

from lib.paypal.client import Client
from lib.paypal.forms import GetPermissonURL


class GetPermissionURLResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'permission-url'
        list_allowed_methods = ['post']

    def obj_create(self, bundle, request, **kwargs):
        form = GetPermissonURL(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        paypal = Client()
        bundle.data = paypal.get_permission_url(*form.args())
        return bundle

