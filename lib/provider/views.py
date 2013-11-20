from curling.lib import HttpClientError
from rest_framework.response import Response

import client
from django_statsd.clients import statsd
from errors import NoReference
from solitude.base import BaseAPIView
from solitude.logger import getLogger

log = getLogger('s.provider')


class NotImplementedView(BaseAPIView):
    pass


class ProxyView(BaseAPIView):
    """
    This view does very little except pass the incoming API call
    straight onto the provider backend that it is a proxy too.

    TODO:
    -   what happens to deeper urls, eg: /provider/ref/sellers/1/?
    """

    def initial(self, request, *args, **kwargs):
        super(ProxyView, self).initial(request, *args, **kwargs)
        self.reference_name = kwargs.pop('reference_name')
        self.proxy = self._get_client(*args, **kwargs)

    def _get_client(self, *args, **kwargs):
        api = client.get_client(self.reference_name).api
        if not api:
            log.info('No reference found: {0}'.format(self.reference_name))
            raise NoReference(self.reference_name)
        if 'uuid' in kwargs:
            return getattr(api, kwargs['resource_name'])(kwargs['uuid'])
        else:
            return getattr(api, kwargs['resource_name'])

    def _make_response(self, proxied_endpoint, args=[], kwargs={}):
        method = getattr(proxied_endpoint, '__name__', 'unknown_method')
        try:
            with statsd.timer('solitude.provider.{ref}.proxy.{method}'
                              .format(ref=self.reference_name,
                                      method=method)):
                return Response(proxied_endpoint(*args, **kwargs))
        except HttpClientError, exc:

            url = getattr(exc.response.request, 'full_url', 'unknown_url')
            log.exception('Proxy exception for {method} on {url}'
                          .format(method=method, url=url))

            data = getattr(exc.response, 'json', None)
            if data:
                proxy_error = data
            else:
                proxy_error = exc.response.content
            return Response({'proxy_error': proxy_error},
                            status=exc.response.status_code)

    def get(self, request, *args, **kwargs):
        return self._make_response(self.proxy.get,
                                   kwargs=request.QUERY_PARAMS.dict())

    def post(self, request, *args, **kwargs):
        # Just piping request.DATA through isn't great but it will do for the
        # moment.
        return self._make_response(self.proxy.post,
                                   args=[request.DATA])

    def put(self, request, *args, **kwargs):
        return self._make_response(self.proxy.put,
                                   args=[request.DATA])

    def delete(self, request, *args, **kwargs):
        return self._make_response(self.proxy.delete)
