from rest_framework.decorators import api_view
from rest_framework.response import Response

from lib.bango.errors import BangoError
from lib.bango.forms import GetEmailAddressesForm, GetLoginTokenForm
from lib.bango.views.base import BangoResource


@api_view(['POST'])
def login(request):
    """
    Retrieve package's infos from the package id
    to be able to later retrieve the authentication token
    given that we do not store any emails/persons ids.
    """
    view = BangoResource()
    form = GetEmailAddressesForm(request.DATA)
    if not form.is_valid():
        return view.form_errors(form)

    try:
        address = view.client('GetEmailAddresses', form.cleaned_data)
    except BangoError, exc:
        return view.client_errors(exc)

    form = GetLoginTokenForm(data={
        'packageId': form.cleaned_data['packageId'],
        'emailAddress': address.adminEmailAddress,
        'personId': address.adminPersonId,
    })
    if not form.is_valid():
        return view.form_errors(form)

    try:
        token = view.client('GetAutoAuthenticationLoginToken',
                            form.cleaned_data)
    except BangoError, exc:
        return view.client_errors(exc)

    return Response({
        'authentication_token': token.authenticationToken,
        'person_id': address.adminPersonId,
        'email_address': address.adminEmailAddress,
    })
