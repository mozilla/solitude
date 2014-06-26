from rest_framework.response import Response

from lib.provider.serializers import (SellerProductReferenceSerializer,
                                      SellerReferenceSerializer)
from lib.provider.views import ProxyView

from solitude.logger import getLogger
from django.shortcuts import get_object_or_404

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

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.DATA)

        if serializer.is_valid():
            # Get the remote data.
            self.remote, status = self.result(self.proxy.post,
                                              serializer.remote_data)
            serializer.object.reference_id = self.remote['uuid']
            serializer.object.save()

            # Impose solitude data on top of reference data.
            data = self.remote.copy()
            data.update(serializer.data)
            return Response(data, status=201)

        return Response(serializer.errors, status=400)

    def get(self, request, *args, **kwargs):
        model = self.serializer_class.Meta.model
        self.object = get_object_or_404(model, pk=kwargs['id'])
        serializer = self.serializer_class(self.object)

        # Add in the reference_id to the remote data.
        kwargs = self.kwargs
        kwargs['uuid'] = self.object.reference_id
        assert self.object.reference_id, 'Missing reference_id'

        # Get the remote data, add it in.
        self.proxy = self.client(**kwargs)
        self.remote, status = self.result(self.proxy.get)

        # Impose solitude data on top of reference data.
        data = self.remote.copy()
        data.update(serializer.data)
        return Response(data)


class SellerReferenceView(MashupView):
    serializer_class = SellerReferenceSerializer


class SellerProductReferenceView(MashupView):
    serializer_class = SellerProductReferenceSerializer
