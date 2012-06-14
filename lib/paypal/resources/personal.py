from cached import Resource

from lib.paypal.forms import GetPersonal


class CheckPersonalBasic(Resource):

    class Meta(Resource.Meta):
        resource_name = 'personal-basic'
        list_allowed_methods = ['post']
        form = GetPersonal
        method = 'get_personal_basic'


class CheckPersonalAdvanced(Resource):

    class Meta(Resource.Meta):
        resource_name = 'personal-advanced'
        list_allowed_methods = ['post']
        form = GetPersonal
        method = 'get_personal_advanced'
