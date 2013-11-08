import json

from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound
from django.views.generic import View

from .client import get_client
from solitude.base import colorize, log_cef
from solitude.logger import getLogger

log = getLogger('s.zippy')


class NoReference(Exception):
    pass


class ZippyView(View):

    def dispatch(self, request, *args, **kwargs):
        """
        Overwrite so we can add log_cef.
        """
        if request.method.lower() in self.http_method_names:
            handler = getattr(self, request.method.lower(),
                              self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed

        # Log the call with CEF and logging.
        if settings.DUMP_REQUESTS:
            print colorize('brace', request.method), request.get_full_path()
        else:
            log.info('%s %s' % (colorize('brace', request.method),
                                request.get_full_path()))

        msg = '%s:%s' % (kwargs.get('reference_name', 'unknown'),
                         kwargs.get('resource_name', 'unknown'))
        log_cef(msg, request, severity=2)

        try:
            return handler(request, *args, **kwargs)
        except NoReference:
            return HttpResponseNotFound()

    def clean_data(self, request):
        """
        Only validate data for solitude related checks.
        """
        return request.POST


class APIView(ZippyView):

    def _get_client(self, name):
        api = get_client(name).api
        if not api:
            log.info('No reference found: {0}'.format(name))
            raise NoReference(name)
        return api

    def get(self, request, *args, **kwargs):
        api = self._get_client(kwargs['reference_name'])
        res = getattr(api, kwargs['resource_name']).get()
        return HttpResponse(json.dumps(res),
                            **{'content_type': 'application/json'})

    def post(self, request, *args, **kwargs):
        api = self._get_client(kwargs['reference_name'])
        data = self.clean_data(request)
        res = getattr(api, kwargs['resource_name']).post(data)
        return HttpResponse(json.dumps(res),
                            **{'content_type': 'application/json'})

api_view = APIView.as_view()
