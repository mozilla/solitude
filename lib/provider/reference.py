from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from lib.provider.serializers import (SellerProductReferenceSerializer,
                                      SellerReferenceSerializer,
                                      TermsSerializer)
from lib.provider.views import ProxyView
from lib.sellers.models import SellerProductReference, SellerReference
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
        self.object = get_object_or_404(model, pk=self.kwargs['pk'])
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


class MashupViewSet(viewsets.ModelViewSet):
    """
    Take a viewset and wrap it into a Mashup.
    """
    reference_name = 'reference'
    resource_name = ''
    serializer_class = ''

    def mashup(self, request, *args, **kwargs):
        proxy = MashupView()
        proxy.serializer_class = self.serializer_class
        proxy.initial(request, reference_name=self.reference_name,
                      resource_name=self.resource_name, *args, **kwargs)
        return proxy

    def create(self, request, *args, **kwargs):
        return self.mashup(request, *args, **kwargs).post(request)

    def retrieve(self, request, *args, **kwargs):
        return self.mashup(request, *args, **kwargs).get(request)

    def update(self, request, *args, **kwargs):
        return self.mashup(request, *args, **kwargs).put(request)

    def delete(self, request, *args, **kwargs):
        raise PermissionDenied


class SellerReference(MashupViewSet):
    model = SellerReference
    resource_name = 'sellers'
    serializer_class = SellerReferenceSerializer


class SellerProductReference(MashupViewSet):
    model = SellerProductReference
    resource_name = 'products'
    serializer_class = SellerProductReferenceSerializer
    filter_fields = ('seller_product__seller', 'seller_product__external_id')
    # Note: that retrieve and list return different results, you might
    # need to do a list and then retrieve.


class Terms(MashupViewSet):
    model = SellerReference
    resource_name = 'terms'
    serializer_class = TermsSerializer
