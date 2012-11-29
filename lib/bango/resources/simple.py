from cached import SimpleResource

from lib.bango.forms import (CreateBankDetailsForm, MakePremiumForm,
                             UpdateRatingForm)


class CreateBankDetailsResource(SimpleResource):

    class Meta(SimpleResource.Meta):
        resource_name = 'bank'
        simple_form = CreateBankDetailsForm
        simple_api = 'CreateBankDetails'


class UpdateRatingResource(SimpleResource):

    class Meta(SimpleResource.Meta):
        resource_name = 'update-rating'
        simple_form = UpdateRatingForm
        simple_api = 'UpdateRating'


class MakePremiumResource(SimpleResource):

    class Meta(SimpleResource.Meta):
        resource_name = 'make-premium'
        simple_form = MakePremiumForm
        simple_api = 'MakePremiumPerAccess'
