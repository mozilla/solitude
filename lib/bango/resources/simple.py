from tastypie.exceptions import ImmediateHttpResponse
from tastypie.http import HttpNoContent

from cached import SimpleResource

from lib.bango.constants import BANGO_ALREADY_PREMIUM_ENABLED
from lib.bango.errors import BangoFormError
from lib.bango.forms import (CreateBankDetailsForm, MakePremiumForm,
                             UpdateRatingForm)


class CreateBankDetailsResource(SimpleResource):

    error_lookup = {
        'INVALID_COUNTRYISO': 'bankAddressIso',
    }

    class Meta(SimpleResource.Meta):
        resource_name = 'bank'
        simple_form = CreateBankDetailsForm
        simple_api = 'CreateBankDetails'


class UpdateRatingResource(SimpleResource):

    error_lookup = {
        'INVALID_RATING': 'rating',
        'INVALID_RATING_SCHEME': 'ratingScheme',
    }

    class Meta(SimpleResource.Meta):
        resource_name = 'rating'
        simple_form = UpdateRatingForm
        simple_api = 'UpdateRating'


class MakePremiumResource(SimpleResource):

    error_lookup = {
        'INVALID_COUNTRYISO': 'currencyIso',
    }

    class Meta(SimpleResource.Meta):
        resource_name = 'premium'
        simple_form = MakePremiumForm
        simple_api = 'MakePremiumPerAccess'

    def obj_create(self, *args, **kwargs):
        try:
            res = super(MakePremiumResource, self).obj_create(*args,
                        raise_on=(BANGO_ALREADY_PREMIUM_ENABLED,), **kwargs)
        except BangoFormError, exc:
            # No need to fail if this is called twice, just catch and continue.
            if exc.id == BANGO_ALREADY_PREMIUM_ENABLED:
                # Normally this method will return a 201 created. I'm not sure
                # what status code best represents this, but a 204 is still a
                # success and allows you to distinguish it, should you want to.
                raise ImmediateHttpResponse(response=HttpNoContent())
            raise
        return res
