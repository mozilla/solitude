import sys

from django.shortcuts import render_to_response
from solitude.base import handle_500


def home(request):
    return render_to_response('home.html')


def error(request, status=500):
    # If they posted JSON, return the error as JSON, assuming that accept
    # is set correctly.
    if request.META['CONTENT_TYPE'] == 'application/json':
        return handle_500(request, sys.exc_info()[1])

    response = render_to_response('error.html')
    response.status_code = status
    return response


def error_403(request):
    return error(request, status=403)


def error_404(request):
    return error(request, status=404)
