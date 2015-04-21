from rest_framework.decorators import api_view
from rest_framework.response import Response

from lib.bango.errors import BangoError, BangoImmediateError, ProcessError
from lib.bango.forms import UpdateRatingForm
from lib.bango.serializers import SellerProductBangoOnly
from lib.bango.views.base import BangoResource


@api_view(['POST'])
def rating(request):
    view = BangoResource()
    view.error_lookup = {
        'INVALID_RATING': 'rating',
        'INVALID_RATING_SCHEME': 'ratingScheme',
    }
    try:
        serial, form = view.process(
            serial_class=SellerProductBangoOnly,
            form_class=UpdateRatingForm,
            request=request)
    except ProcessError, exc:
        return exc.response

    data = form.cleaned_data
    data['bango'] = serial.object['seller_product_bango'].bango_id
    if not data['bango']:
        # Note: that this error formatting seems quite inconsistent
        # with the rest of the errors. Something we should clean up.
        raise BangoImmediateError(
            {'seller_product_bango':
             ['Empty bango_id for: {0}'
              .format(serial.object['seller_product_bango'].pk)]})

    try:
        view.client('UpdateRating', data)
    except BangoError, exc:
        return view.client_errors(exc)

    return Response(form.cleaned_data)
