from rest_framework.response import Response

from errors import NoReference
from client import get_client
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
        api = get_client(kwargs['reference_name']).api
        if not api:
            log.info('No reference found: {0}'
                     .format(kwargs['reference_name']))
            raise NoReference(kwargs['reference_name'])
        if 'uuid' in kwargs:
            return getattr(api, kwargs['resource_name'])(kwargs['uuid'])
        else:
            return getattr(api, kwargs['resource_name'])

    def get(self, request, *args, **kwargs):
        return Response(self.proxy.get())

    def post(self, request, *args, **kwargs):
        # Just piping request.DATA through isn't great but it will do for the
        # moment.
        return Response(self.proxy.post(request.DATA))

    def put(self, request, *args, **kwargs):
        return Response(self.proxy.put(request.DATA))

    def delete(self, request, *args, **kwargs):
        return Response(self.proxy.delete())
