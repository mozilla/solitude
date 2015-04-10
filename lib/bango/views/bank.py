from rest_framework.decorators import api_view
from rest_framework.response import Response

from lib.bango.errors import BangoError, ProcessError
from lib.bango.forms import CreateBankDetailsForm
from lib.bango.serializers import SellerBangoOnly
from lib.bango.views.base import BangoResource


@api_view(['POST'])
def bank(request):
    view = BangoResource()
    view.error_lookup = {
        'INVALID_COUNTRYISO': 'bankAddressIso',
    }

    try:
        serial, form = view.process(
            serial_class=SellerBangoOnly,
            form_class=CreateBankDetailsForm,
            request=request)
    except ProcessError, exc:
        return exc.response

    data = form.cleaned_data

    try:
        view.client('CreateBankDetails', data)
    except BangoError, exc:
        return view.client_errors(exc)

    return Response(form.cleaned_data)
