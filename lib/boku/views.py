from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from lib.boku.forms import BokuTransactionForm, BokuServiceForm
from lib.boku.serializers import (SellerBokuSerializer,
                                  SellerProductBokuSerializer)
from lib.sellers.models import SellerBoku, SellerProductBoku
from solitude.base import BaseAPIView
from solitude.logger import getLogger


log = getLogger('s.boku')


class SellerBokuViewSet(viewsets.ModelViewSet):
    model = SellerBoku
    serializer_class = SellerBokuSerializer

    def destroy(self, request, pk=None):
        raise PermissionDenied


class SellerProductBokuViewSet(viewsets.ModelViewSet):
    model = SellerProductBoku
    serializer_class = SellerProductBokuSerializer
    filter_fields = ('seller_product',)

    def destroy(self, request, pk=None):
        instance = self.get_object()
        log.info((
            'Deleting SellerProductBoku {id} for boku '
            'account {account_id} and product {product_id}'
        ).format(
            id=instance.pk,
            account_id=instance.seller_boku.id,
            product_id=instance.seller_product.public_id
        ))
        return super(SellerProductBokuViewSet, self).destroy(request, pk=pk)


class BokuTransactionView(BaseAPIView):

    def post(self, request):
        form = BokuTransactionForm(request.DATA)

        if form.is_valid():
            transaction = form.start_transaction()
            log.info(('Successfully started Boku Transaction: '
                      '{transaction_id}').format(
                transaction_id=transaction['transaction_id'],
            ))
            return Response(transaction)
        else:
            log.error('Failed to start Boku Transaction: {errors}'.format(
                errors=form.errors.as_text(),
            ))
            return self.form_errors(form)


class BokuVerifyServiceView(BaseAPIView):

    def post(self, request):
        form = BokuServiceForm(request.DATA)

        if form.is_valid():
            log.info(('Successfully verified Boku service id: '
                      '{service_id}').format(
                service_id=form.cleaned_data['service_id'],
            ))
            return Response(status=204)
        else:
            log.error('Failed to verify Boku Service ID: {errors}'.format(
                errors=form.errors.as_text(),
            ))
            return self.form_errors(form)
