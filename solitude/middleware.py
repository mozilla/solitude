import threading

_local = threading.local()


def get_oauth_key():
    return getattr(_local, 'OAUTH_KEY', '<anon>')


def get_transaction_id():
    return getattr(_local, 'TRANSACTION_ID', None)


class LoggerMiddleware(object):

    def process_request(self, request):
        _local.TRANSACTION_ID = request.META.get('HTTP_TRANSACTION_ID', '-')
        _local.OAUTH_KEY = getattr(request, 'OAUTH_KEY', '<anon>')
