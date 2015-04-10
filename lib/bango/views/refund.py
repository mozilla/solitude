import uuid
from functools import partial

from django.conf import settings

from rest_framework.response import Response

from lib.bango.client import ClientMock
from lib.bango.constants import CANT_REFUND, NOT_SUPPORTED, OK, PENDING
from lib.bango.errors import BangoAnticipatedError
from lib.bango.forms import RefundForm, RefundStatusForm
from lib.bango.serializers import EasyObject, RefundSerializer
from lib.bango.views.base import BangoResource
from lib.transactions.constants import (STATUS_COMPLETED, STATUS_FAILED,
                                        STATUS_PENDING, TYPE_REFUND,
                                        TYPE_REFUND_MANUAL)
from lib.transactions.models import Transaction
from solitude.base import NonDeleteModelViewSet
from solitude.logger import getLogger

log = getLogger('s.bango.refund')


class RefundViewSet(NonDeleteModelViewSet, BangoResource):

    """
    A specific resource for creating refunds and then checking the state of
    that refund against Bango. Since a transaction is created, you can examine
    the state of the transaction in solitude without having to check against
    Bango.
    """

    serializer_class = RefundSerializer
    queryset = Transaction.objects.filter()

    def update(self):
        return Response(status=405)

    def get_client(self, extra, fake=False):
        """
        A wrapper around the original client call to allow us to return a Mock
        object for refunds. See bug 845332 and bug 936242 for more information.
        """
        fake = fake or getattr(settings, 'BANGO_FAKE_REFUNDS', None)
        if fake:
            log.info('Faking out refunds')
            res = extra.get('fake_response', {})
            client = ClientMock()
            if not res:
                # We'll be just using the default mock defined on the object.
                log.warning('"fake_response" not defined, using default')
            else:
                log.info('"fake_response" being used')
                client.mock_results = partial(client.mock_results, data=res)
            return client

    def list(self, request, *args, **kwargs):
        form = RefundStatusForm(request.DATA)
        if not form.is_valid():
            return self.form_errors(form)

        transaction = form.cleaned_data['uuid']
        is_manual = transaction.type == TYPE_REFUND_MANUAL

        try:
            res = self.client(
                'GetRefundStatus',
                {'refundTransactionId': transaction.uid_pay},
                raise_on=(PENDING, CANT_REFUND, NOT_SUPPORTED),
                client=self.get_client(request.DATA, fake=is_manual)
            )
        except BangoAnticipatedError, exc:
            res = EasyObject(
                responseCode=exc.id,
                responseMessage=exc.message,
                refundTransactionId='')

        code = res.responseCode
        log.info('Transaction %s: %s' % (code, transaction.pk))

        # Alter our transaction if we need to.
        if code == OK and transaction.status != STATUS_COMPLETED:
            log.info('Status updated to %s: %s' % (code, transaction.pk))
            transaction.status = STATUS_COMPLETED
            transaction.save()

        elif code == PENDING and transaction.status != STATUS_PENDING:
            log.info('Status updated to %s: %s' % (code, transaction.pk))
            transaction.status = STATUS_PENDING
            transaction.save()

        elif (code in (CANT_REFUND, NOT_SUPPORTED) and
              transaction.status != STATUS_FAILED):
            log.info('Status updated to %s: %s' % (code, transaction.pk))
            transaction.status = STATUS_FAILED
            transaction.save()

        # Quick hack to get this on the serializer object.
        transaction._bango_refund_response_code = code
        return Response(RefundSerializer(instance=transaction).data)

    def create(self, request, *args, **kw):
        form = RefundForm(request.DATA)
        if not form.is_valid():
            return self.form_errors(form)

        obj = form.cleaned_data['uuid']
        manual = form.cleaned_data['manual']
        external_uuid = str(uuid.uuid4())

        try:
            res = self.client(
                'DoRefund', {
                    'bango': obj.seller_product.product.bango_id,
                    'externalTransactionId': external_uuid,
                    'refundType': 'OPERATOR',
                    'transactionId': obj.uid_support
                },
                raise_on=(PENDING,),
                client=self.get_client(request.DATA, fake=manual)
            )
        except BangoAnticipatedError, exc:
            # We haven't been able to get a response back that is pending
            # so I'm not sure if the refundTransactionId is there. Check
            # this.
            res = EasyObject(
                responseCode=exc.id,
                responseMessage=exc.message,
                refundTransactionId='todo')

        code = res.responseCode
        status = {
            OK: STATUS_COMPLETED,
            PENDING: STATUS_PENDING
        }

        # If that succeeded, create a new transaction for the refund.
        transaction = Transaction.objects.create(
            amount=obj.amount,
            buyer=obj.buyer,
            currency=obj.currency,
            provider=obj.provider,
            related=obj,
            seller_product=obj.seller_product,
            # Note: check on this when we can actually do refunds, but for
            # the moment we'll assume they go straight through.
            status=status.get(res.responseCode),
            source='',
            type=TYPE_REFUND_MANUAL if manual else TYPE_REFUND,
            uuid=external_uuid,
            uid_pay=res.refundTransactionId)

        transaction._bango_refund_response_code = code
        return Response(RefundSerializer(instance=transaction).data)
