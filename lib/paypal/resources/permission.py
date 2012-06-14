from cached import Resource

from lib.paypal.client import Client
from lib.paypal.forms import CheckPermission, GetPermissionURL


class PermissionResource(Resource):

    def obj_create(self, bundle, request, **kwargs):
        form = self._meta.form(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        paypal = Client()
        bundle.data = getattr(paypal, self._meta.method)(*form.args())
        return bundle


class GetPermissionURLResource(PermissionResource):

    class Meta(PermissionResource.Meta):
        resource_name = 'permission-url'
        list_allowed_methods = ['post']
        form = GetPermissionURL
        method = 'get_permission_url'


class CheckPermissionResource(PermissionResource):

    class Meta(PermissionResource.Meta):
        resource_name = 'permission-check'
        list_allowed_methods = ['post']
        form = CheckPermission
        method = 'check_permission'
