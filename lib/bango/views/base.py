from rest_framework.response import Response

from lib.bango.client import format_client_error, get_client
from lib.bango.errors import (
    BangoAnticipatedError, BangoImmediateError, BangoUnanticipatedError,
    ProcessError)
from solitude.base import format_form_errors


class BangoResource(object):

    def client(self, method, data, raise_on=None, client=None):
        """
        Client to call the bango client and process errors in a way that
        is relevant to the form. If you pass in a list of errors, these will
        be treated as errors the callee is going to deal with and will not
        be returning ImmediateHttpResponses. Instead the callee will have to
        cope with these BangoAnticipatedErrors as appropriate.

        You can optionally pass in a client to override the default.
        """
        raise_on = raise_on or []
        try:
            return getattr(client or get_client(), method)(data)
        except BangoUnanticipatedError, exc:
            # It was requested that the error that was passed in
            # was actually anticipated, so let's raise that type of error.
            if exc.id in raise_on:
                raise BangoAnticipatedError(exc.id, exc.message)

            res = self.client_errors(exc)
            raise BangoImmediateError(format_form_errors(res))

    def process(self, serial_class, form_class, request):
        form = form_class(request.DATA)
        if not form.is_valid():
            raise ProcessError(Response(format_form_errors(form), status=400))

        serial = serial_class(data=request.DATA)
        if not serial.is_valid():
            raise ProcessError(Response(serial.errors, status=400))

        return serial, form

    def client_errors(self, exc):
        key = getattr(self, 'error_lookup', {}).get(exc.id, '__all__')
        return format_client_error(key, exc)

    def form_errors(self, forms):
        return Response(format_form_errors(forms), status=400)
