from django.shortcuts import get_object_or_404

from rest_framework.response import Response

from lib.provider.serializers import (SellerProductReferenceSerializer,
                                      SellerReferenceSerializer,
                                      TermsSerializer)
from lib.provider.views import ProxyView
from solitude.logger import getLogger

log = getLogger('s.provider')


class MashupView(ProxyView):
    """
    Overrides the normal proxy view to first process the data locally
    and then remotely, storing data in reference_id fields on the
    objects.

    This allows clients interacting with solitude to make one call which
    hits solitude and the back end server, limiting the amount of knowledge
    the client has to have about the backend service, such as zippy.
    """
    _proxy_reset = False

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.DATA)

        if serializer.is_valid():
            # Get the remote data.
            self.remote, status = self.result(self.get_proxy().post,
                                              serializer.remote_data)
            serializer.object.reference_id = self.remote['uuid']
            serializer.object.save()

            serializer.data['reference'] = self.remote
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)

    def get(self, request, *args, **kwargs):
        self.get_object()
        serializer = self.serializer_class(self.object)

        self.remote, status = self.result(self.get_proxy().get)

        serializer.data['reference'] = self.remote
        return Response(serializer.data, status=200)

    def get_object(self):
        """
        Shortcut to get the object based on the serializer.
        Each time this is called, the proxy will be reset so that new
        calls to get_proxy will calculate their URL based on the value
        retreived here.
        """
        model = self.serializer_class.Meta.model
        self.object = get_object_or_404(model, pk=self.kwargs['id'])
        self._proxy_reset = True

    def get_proxy(self):
        """
        On GET requests, we have to calculate the correct URL in the
        reference implementation. The request into solitude is based
        on the solitude primary key. So this finds the reference_id that
        was returned to us and uses that for the URL for the
        reference implementation.
        """
        if not self._proxy_reset:
            return self.proxy

        kwargs = self.kwargs
        kwargs['uuid'] = self.object.reference_id
        assert self.object.reference_id, 'Missing reference_id'
        self._proxy_reset = False
        self.proxy = self.client(**kwargs)
        return self.proxy

    def put(self, request, *args, **kwargs):
        self.get_object()
        serializer = self.serializer_class(self.object, data=request.DATA)

        if serializer.is_valid():
            self.remote, status = self.result(self.get_proxy().put,
                                              serializer.remote_data)
            # Update the record locally and return.
            serializer.object.save()

            serializer.data['reference'] = self.remote
            return Response(serializer.data, status=200)

        return Response(serializer.errors, status=400)


class SellerReferenceView(MashupView):
    serializer_class = SellerReferenceSerializer


class SellerProductReferenceView(MashupView):
    serializer_class = SellerProductReferenceSerializer


class Terms(MashupView):
    serializer_class = TermsSerializer
