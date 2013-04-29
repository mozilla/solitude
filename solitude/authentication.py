import logging
from urlparse import urljoin


from django.conf import settings
import oauth2

from tastypie.authentication import Authentication

log = logging.getLogger('s.auth')


class Consumer(object):

    def __init__(self, key, secret=None):
        self.key = key
        self.secret = secret or settings.CLIENT_OAUTH_KEYS[key]


class OAuthError(RuntimeError):
    def __init__(self, message='OAuth error occured.'):
        self.message = message


class OAuthAuthentication(Authentication):
    """
    This is based on https://github.com/amrox/django-tastypie-two-legged-oauth
    with permission.
    """

    def __init__(self, realm='', consumer=None):
        self.realm = realm
        self.consumer = consumer

    def _header(self, request):
        return request.META.get('HTTP_AUTHORIZATION', None)

    def is_authenticated(self, request, **kwargs):
        auth_header_value = self._header(request)
        oauth_server, oauth_request = initialize_oauth_server_request(request)
        try:
            key = get_oauth_consumer_key_from_header(auth_header_value)
            if not key:
                if settings.REQUIRE_OAUTH:
                    return False
                return True
            oauth_server.verify_request(oauth_request, Consumer(key), None)
            log.info(u'Access granted: %s' % key)
            return True

        except KeyError:
            log.error(u'No key: %s' % key)
            return False

        except:
            log.error(u'Access failed: %s' % key, exc_info=True)
            return False


def initialize_oauth_server_request(request):
    """
    OAuth initialization.
    """

    # Since 'Authorization' header comes through as 'HTTP_AUTHORIZATION',
    # convert it back.
    auth_header = {}
    if 'HTTP_AUTHORIZATION' in request.META:
        auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION')}

    if not settings.SITE_URL:
        raise ValueError('SITE_URL cannot be blank')

    url = urljoin(settings.SITE_URL, request.path)

    # Note: we are only signing using the QUERY STRING. We are not signing the
    # body yet. According to the spec we should be including an oauth_body_hash
    # as per:
    #
    # http://oauth.googlecode.com/svn/spec/ext/body_hash/1.0/drafts/1/spec.html
    #
    # There is no support in python-oauth2 for this yet. There is an
    # outstanding pull request for this:
    #
    # https://github.com/simplegeo/python-oauth2/pull/110
    #
    # Or time to move to a better OAuth implementation.
    method = getattr(request, 'signed_method', request.method)
    oauth_request = oauth2.Request.from_request(
            method, url, headers=auth_header,
            query_string=request.META['QUERY_STRING'])
    oauth_server = oauth2.Server(signature_methods={
        'HMAC-SHA1': oauth2.SignatureMethod_HMAC_SHA1()
        })
    return oauth_server, oauth_request


def get_oauth_consumer_key_from_header(auth_header_value):
    key = None

    # Process Auth Header
    if not auth_header_value:
        return None
    # Check that the authorization header is OAuth.
    if auth_header_value[:6] == 'OAuth ':
        auth_header = auth_header_value[6:]
        try:
            # Get the parameters from the header.
            header_params = oauth2.Request._split_header(auth_header)
            if 'oauth_consumer_key' in header_params:
                key = header_params['oauth_consumer_key']
        except:
            raise OAuthError('Unable to parse OAuth parameters from '
                    'Authorization header.')
    return key
