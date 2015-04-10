from rest_framework.decorators import api_view
from rest_framework.response import Response

from lib.bango.constants import BANGO_ALREADY_PREMIUM_ENABLED
from lib.bango.errors import (
    BangoAnticipatedError, BangoError, BangoImmediateError, ProcessError)
from lib.bango.forms import MakePremiumForm
from lib.bango.serializers import SellerProductBangoOnly
from lib.bango.views.base import BangoResource


@api_view(['POST'])
def premium(request):
    view = BangoResource()
    view.error_lookup = {
        'INVALID_COUNTRYISO': 'currencyIso',
    }

    try:
        serial, form = view.process(
            serial_class=SellerProductBangoOnly,
            form_class=MakePremiumForm,
            request=request)
    except ProcessError, exc:
        return exc.response

    data = form.cleaned_data
    data['bango'] = serial.object['seller_product_bango'].bango_id
    if not data['bango']:
        # Note: that this error formatting seems quite inconsistent
        # with the rest of the errors. Something we should clean up.
        # https://github.com/mozilla/solitude/issues/349
        raise BangoImmediateError(
            {'seller_product_bango':
             ['Empty bango_id for: {0}'
              .format(serial.object['seller_product_bango'].pk)]}
        )

    try:
        view.client('MakePremiumPerAccess', data,
                    raise_on=[BANGO_ALREADY_PREMIUM_ENABLED])
    except BangoAnticipatedError, exc:
        # This can occur and is expected, will return a 204 instead of
        # a 200 to distinguish in the client if you need to.
        return Response(status=204)
    except BangoError, exc:
        return view.client_errors(exc)

    return Response(form.cleaned_data)
