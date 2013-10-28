import threading

_local = threading.local()


def get_oauth_key():
    return getattr(_local, 'OAUTH_KEY', '<anon>')


def get_transaction_id():
    return getattr(_local, 'TRANSACTION_ID', None)


def set_oauth_key(key):
    _local.OAUTH_KEY = key


class LoggerMiddleware(object):

    def process_request(self, request):
        _local.TRANSACTION_ID = request.META.get('HTTP_TRANSACTION_ID', '-')
        # At the beginning of the request we won't have done authentication
        # yet so this sets the value to anon. When authentication is completed
        # that will update the oauth_key with the authenticated value.
        set_oauth_key(getattr(request, 'OAUTH_KEY', '<anon>'))
