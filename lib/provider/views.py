import json

from django.core.urlresolvers import reverse

from django_statsd.clients import statsd
from rest_framework.response import Response

import client
from curling.lib import HttpClientError
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
        self.proxy = self.client(*args, **kwargs)
        self.kwargs = kwargs # Store this incase we need to recreate it later.

    def client(self, *args, **kwargs):
        api = client.get_client(self.reference_name).api
        if not api:
            log.info('No reference found: {0}'.format(self.reference_name))
            raise NoReference(self.reference_name)
        if 'uuid' in kwargs:
            return getattr(api, kwargs['resource_name'])(kwargs['uuid'])
        else:
            return getattr(api, kwargs['resource_name'])

    def resource(self, result):
        """
        Turns Zippy's resource into a solitude one.
        """
        if 'resource_uri' in result:
            # TODO: this maps everything into the generic view, let's remove
            # this.
            result['resource_uri'] = reverse('provider.api_view', kwargs={
                'reference_name': self.reference_name,
                'resource_name': result['resource_name'],
                'uuid': result['resource_pk'],
            })
            if not result['resource_uri'].endswith('/'):
                result['resource_uri'] = result['resource_uri'] + '/'
        if 'resource_pk' in result:
            result['id'] = result.pop('resource_pk')
        return result

    def error(self, response):
        """
        Turns Zippy's error into a solitude one.
        """
        try:
            message = response.json['error']['message']
        except KeyError:
            message = response.json
        return {'error_message': message}

    def result(self, proxied_endpoint, *args, **kwargs):
        method = getattr(proxied_endpoint, '__name__', 'unknown_method')
        try:
            with statsd.timer('solitude.provider.{ref}.proxy.{method}'
                              .format(ref=self.reference_name,
                                      method=method)):
                result = proxied_endpoint(*args, **kwargs)
                # It looks like the proxied endpoint does not return a status
                # so we'll assume its a 200. That's not great.
                return self.resource(result), 200
        except HttpClientError, exc:
            url = getattr(exc.response.request, 'full_url', 'unknown_url')
            log.exception('Proxy exception for {method} on {url}'
                          .format(method=method, url=url))
            raise

    def response(self, proxied_endpoint, args=None, kwargs=None):
        args = args or []
        kwargs = kwargs or {}
        try:
            result, status = self.result(proxied_endpoint, *args, **kwargs)
        except HttpClientError, exc:
            return Response(self.error(exc.response),
                            status=exc.response.status_code)
        return Response(result, status=status)

    def get(self, request, *args, **kwargs):
        return self.response(self.proxy.get,
                             kwargs=request.QUERY_PARAMS.dict())

    def post(self, request, *args, **kwargs):
        return self.response(self.proxy.post, args=[request.DATA])

    def put(self, request, *args, **kwargs):
        return self.response(self.proxy.put, args=[request.DATA])

    def delete(self, request, *args, **kwargs):
        return self.response(self.proxy.delete)
