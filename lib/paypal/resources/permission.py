from cached import Resource
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
        form = GetPermissionToken
        method = 'get_permission_token'
