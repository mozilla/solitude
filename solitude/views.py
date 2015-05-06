import sys

from django.http import HttpResponse, JsonResponse

from solitude.base import log_cef


def home(request):
    return response(request,
                    data={'message': 'A home page in solitude.'},
                    status=200)


def response(request, status=500, data=None):
    # If returning JSON, then we can't send back an empty body, unless we
    # return a 204 - the client should be able to parse it.
    message = data if data else {}
    if 'application/json' in request.META.get('HTTP_ACCEPT'):
        return JsonResponse(message, status=status)

    # If you send back something flasy dictionary with HTTPResponse, it just
    # returns an empty body.
    return HttpResponse(message.values(), status=status)


def error_500(request):
    exception = sys.exc_info()[1]
    log_cef(str(exception), request, severity=3)
    return response(request, status=500,
                    data={'error': exception.__class__.__name__})


def error_403(request):
    return response(request, status=403)


def error_404(request):
    return response(request, status=404)
