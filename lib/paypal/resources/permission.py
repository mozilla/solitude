from cached import Resource

from lib.paypal.client import get_client
from lib.paypal.forms import (CheckPermission, GetPermissionToken,
                              GetPermissionURL)


class GetPermissionURLResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'permission-url'
        list_allowed_methods = ['post']
        form = GetPermissionURL
        method = 'get_permission_url'


class CheckPermissionResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'permission-check'
        list_allowed_methods = ['post']
        form = CheckPermission
        method = 'check_permission'


class GetPermissionTokenResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'permission-token'
        list_allowed_methods = ['post']

    def obj_create(self, bundle, request, **kwargs):
        form = GetPermissionToken(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        paypal = get_client()
        result = paypal.get_permission_token(*form.args())
        seller = form.cleaned_data['seller']
        seller.token = result['token']
        seller.secret = result['secret']
        seller.save()
        bundle.obj = seller
        return bundle

    def dehydrate(self, bundle):
        return {'token': bundle.obj.token_exists,
                'secret': bundle.obj.secret_exists}
