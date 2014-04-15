from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from lib.boku.forms import BokuTransactionForm
from lib.boku.serializers import SellerBokuSerializer
from lib.sellers.models import SellerBoku
from solitude.base import BaseAPIView
from solitude.logger import getLogger


log = getLogger('s.boku')


class SellerBokuViewSet(viewsets.ModelViewSet):
    model = SellerBoku
    serializer_class = SellerBokuSerializer

    def destroy(self, request, pk=None):
        raise PermissionDenied


class BokuTransactionView(BaseAPIView):

    def post(self, request):
        form = BokuTransactionForm(request.DATA)

        if form.is_valid():
            transaction = form.start_transaction()
            log.error(('Successfully started Boku Transaction: '
                       '{transaction_id}').format(
                transaction_id=transaction['transaction_id'],
            ))
            return Response(transaction)
        else:
            log.error('Failed to start Boku Transaction: {errors}'.format(
                errors=form.errors,
            ))
            return self.form_errors(form)
