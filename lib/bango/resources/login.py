from rest_framework.decorators import api_view
from rest_framework.response import Response

from lib.bango.errors import BangoError
from lib.bango.forms import GetEmailAddressesForm, GetLoginTokenForm
from lib.bango.client import format_client_error, get_client

from solitude.base import DRFBaseResource


class LoginResource(DRFBaseResource):

    def client(self, method, data, client=None):
        return getattr(client or get_client(), method)(data)

    def client_errors(self, exc):
        return self.form_errors(format_client_error('__all__', exc))


@api_view(['POST'])
def login(request):
    """
    Retrieve package's infos from the package id
    to be able to later retrieve the authentication token
    given that we do not store any emails/persons ids.
    """
    resource = LoginResource()
    form = GetEmailAddressesForm(request.DATA)
    if not form.is_valid():
        return resource.form_errors(form)

    try:
        address = resource.client('GetEmailAddresses', form.cleaned_data)
    except BangoError, exc:
        return resource.client_errors(exc)

    form = GetLoginTokenForm(data={
        'packageId': form.cleaned_data['packageId'],
        'emailAddress': address.adminEmailAddress,
        'personId': address.adminPersonId,
    })
    if not form.is_valid():
        return resource.form_errors(form)

    try:
        token = resource.client('GetAutoAuthenticationLoginToken',
                                form.cleaned_data)
    except BangoError, exc:
        return resource.client_errors(exc)

    return Response({
        'authentication_token': token.authenticationToken,
        'person_id': address.adminPersonId,
        'email_address': address.adminEmailAddress,
    })
