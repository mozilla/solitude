from django.shortcuts import render_to_response


def home(request):
    return render_to_response('home.html')


def error(request, status=500):
    response = render_to_response('error.html')
    response.status_code = status
    return response

def error_403(request):
    return error(request, status=403)

def error_404(request):
    return error(request, status=404)
