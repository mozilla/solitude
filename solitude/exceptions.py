
from django.db.transaction import set_rollback

from rest_framework.response import Response
from rest_framework.views import exception_handler

from lib.bango.errors import BangoImmediateError
from solitude.logger import getLogger

log = getLogger('s')


def custom_exception_handler(exc):
    # If you raise an error in solitude, it comes to here and
    # we rollback the transaction.
    log.info('Handling exception, about to roll back for: {}, {}'
             .format(type(exc), exc.message))
    set_rollback(True)

    if hasattr(exc, 'formatter'):
        try:
            return Response(exc.formatter(exc).format(),
                            status=getattr(exc, 'status_code', 422))
        except:
            # If the formatter fails, fall back to the standard
            # error formatting.
            log.exception('Failed to use formatter.')

    if isinstance(exc, BangoImmediateError):
        return Response(exc.message, status=400)

    return exception_handler(exc)
