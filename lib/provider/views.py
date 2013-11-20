from rest_framework.response import Response

import client
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
    -   what happens when the client throws an error, will that
        be propogated correctly?
    -   what happens to deeper urls, eg: /provider/ref/sellers/1/?
    """

    def initial(self, request, *args, **kwargs):
        super(ProxyView, self).initial(request, *args, **kwargs)
        self.proxy = self._get_client(*args, **kwargs)

    def _get_client(self, *args, **kwargs):
        api = client.get_client(kwargs['reference_name']).api
        if not api:
            log.info('No reference found: {0}'
                     .format(kwargs['reference_name']))
            raise NoReference(kwargs['reference_name'])
        if 'uuid' in kwargs:
            return getattr(api, kwargs['resource_name'])(kwargs['uuid'])
        else:
            return getattr(api, kwargs['resource_name'])

    def _normalize_qs(self, complete_qs):
        # This code looks like it does nothing but that's because complete_qs
        # is a "special" query string object. Its values are lists but we
        # want them as single values. Iterating with items() magically
        # converts the lists to single values.
        qs = {}
        for k, v in complete_qs.items():
            qs[k] = v
        return qs

    def get(self, request, *args, **kwargs):
        qs = self._normalize_qs(request.QUERY_PARAMS)
        return Response(self.proxy.get(**qs))

    def post(self, request, *args, **kwargs):
        # Just piping request.DATA through isn't great but it will do for the
        # moment.
        return Response(self.proxy.post(request.DATA))

    def put(self, request, *args, **kwargs):
        return Response(self.proxy.put(request.DATA))

    def delete(self, request, *args, **kwargs):
        return Response(self.proxy.delete())
