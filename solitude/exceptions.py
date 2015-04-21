from rest_framework.response import Response
from rest_framework.views import exception_handler

from lib.bango.errors import BangoImmediateError


def custom_exception_handler(exc):
    if isinstance(exc, BangoImmediateError):
        return Response(exc.message, status=400)

    return exception_handler(exc)
