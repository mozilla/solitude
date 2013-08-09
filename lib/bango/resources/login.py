from rest_framework import status as http_statuses
from rest_framework.decorators import api_view
from rest_framework.response import Response

from cached import BangoResource
from lib.bango.errors import LoginError
from lib.bango.forms import GetEmailAddressesForm, GetLoginTokenForm


class LoginResource(BangoResource):

    def form_errors(self, form):
        return {'errors': dict(form.errors.items())}


class EmailAddressesResource(LoginResource):

    def get_package_infos(self, request_post):
        form = GetEmailAddressesForm(request_post)
        if not form.is_valid():
            raise LoginError(dict(form.errors.items()))
        resp = self.client('GetEmailAddresses', form.cleaned_data)
        if 'errors' in resp:
            raise LoginError(resp['errors'])
        return {
            'packageId': form.cleaned_data['packageId'],
            'emailAddress': resp['adminEmailAddress'],
            'personId': resp['adminPersonId'],
        }


class TokenResource(LoginResource):

    def get_authentication_token(self, package_infos):
        form = GetLoginTokenForm(data=package_infos)
        if not form.is_valid():
            raise LoginError(dict(form.errors.items()))
        resp = self.client('GetAutoAuthenticationLoginToken',
                           form.cleaned_data)
        if 'errors' in resp:
            raise LoginError(resp['errors'])

        return resp['authenticationToken']


@api_view(['POST'])
def login(request):
    """
    First, retrieving package's infos from the package id
    to be able to later retrieve the authentication token
    given that we do not store any emails/persons ids.
    """
    try:
        resource = EmailAddressesResource()
        package_infos = resource.get_package_infos(request.DATA)
    except LoginError, e:
        return Response(e.message, status=http_statuses.HTTP_400_BAD_REQUEST)
    try:
        resource = TokenResource()
        authentication_token = resource.get_authentication_token(package_infos)
    except LoginError, e:
        return Response(e.message, status=http_statuses.HTTP_400_BAD_REQUEST)

    return Response({
        'authentication_token': authentication_token,
        'person_id': package_infos['personId'],
        'email_address': package_infos['emailAddress'],
    })
