import sys

from django.http import JsonResponse

from solitude.base import log_cef


def home(request):
    return response(request,
                    data={'message': 'A home page in solitude.'},
                    status=200)


def response(request, status=500, data=None):
    # If returning JSON, then we can't send back an empty body, unless we
    # return a 204 - the client should be able to parse it.
    #
    # This assumes the client can receive JSON. We could send a HTTP 406
    # to anyone not accepting JSON, but that seems unusually cruel punishment
    # and will mask the real error.
    message = data if data else {}
    return JsonResponse(message, status=status)


def error_500(request):
    exception = sys.exc_info()[1]
    log_cef(str(exception), request, severity=3)
    return response(request, status=500,
                    data={'error': exception.__class__.__name__})


def error_403(request):
    return response(request, status=403)


def error_404(request):
    return response(request, status=404)
