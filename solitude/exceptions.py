from django.db.transaction import rollback

from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from lib.bango.errors import BangoImmediateError
from lib.brains.errors import BraintreeResultError
from solitude.logger import getLogger

log = getLogger('s')


class InvalidQueryParams(ParseError):
    status_code = 400
    default_detail = 'Incorrect query parameters.'


def custom_exception_handler(exc):
    log.warning('Transaction rolled back due to error.')
    rollback()

    if isinstance(exc, BraintreeResultError):
        res = {
            '__all__': [exc.result.message],
            '__braintree__': 'error',
            '__type__': 'braintree'
        }
        return Response(res, status=400)

    if isinstance(exc, BangoImmediateError):
        return Response(exc.message, status=400)

    return exception_handler(exc)
