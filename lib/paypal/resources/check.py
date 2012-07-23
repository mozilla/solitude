from cached import Resource

from lib.paypal.check import Check
from lib.paypal.forms import AccountCheck


class AccountCheckResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'account-check'
        list_allowed_methods = ['post']

    def obj_create(self, bundle, request, **kwargs):
        form = AccountCheck(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        check = Check(**form.kwargs())
        check.all()
        bundle.data = {'passed': check.passed,
                       'errors': check.errors}
        return bundle
