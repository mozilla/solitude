from django.http import HttpResponse

from rest_framework import viewsets

from lib.boku.constants import TRANS_STATUS_FROM_VERIFY_CODE
from lib.boku.errors import BokuException
from lib.boku.forms import EventForm
from lib.boku.utils import verify
from lib.transactions.constants import (STATUS_COMPLETED, STATUSES_INVERTED)
from solitude.base import BaseAPIView, log_cef
from solitude.logger import getLogger

log = getLogger('s.boku')


class Event(viewsets.ViewSet, BaseAPIView):

    """
    Process a Boku server to server notification.

    See Boku Technical Documentation for an example of the data being
    sent in.
    """

    def create(self, request):
        form = EventForm(request.DATA)
        param = form.data.get('param')

        if not form.is_valid():
            log.info('Notification invalid: {0}'.format(param))
            return self.form_errors([form])

        cleaned = form.cleaned_data
        transaction = cleaned['param']

        # Verify this transaction_id against Boku, this will raise errors
        # if the tranasction_id was not sent by Boku.
        log.info('Verifying notification for Boku transaction id: {0}'
                 .format(transaction))

        status = STATUS_COMPLETED
        try:
            verify(cleaned['trx_id'], cleaned['amount'], cleaned['currency'])
        except BokuException, exc:
            log.info('Got non-zero Boku API response: '
                     '{exc}; code={exc.result_code}; msg={exc.result_msg}'
                     .format(exc=exc))
            # Boku will return non-zero error codes to indicate certain
            # transaction states. These states mean that the notification
            # itself is valid.
            if exc.result_code in TRANS_STATUS_FROM_VERIFY_CODE:
                status = TRANS_STATUS_FROM_VERIFY_CODE[exc.result_code]
                log.info('got Boku transaction status {s} from code {c}'
                         .format(s=status, c=exc.result_code))
            else:
                raise

        old_status = transaction.status
        transaction.status = status
        transaction.amount = cleaned['amount']
        transaction.currency = cleaned['currency']
        transaction.uid_support = cleaned['trx_id']
        transaction.save()

        log_cef('Transaction change success', request, severity=7,
                cs6Label='old', cs6=STATUSES_INVERTED[old_status],
                cs7Label='new', cs7=STATUSES_INVERTED[transaction.status])
        log.info('Transaction {0} changed to {1} from {2}'
                 .format(transaction.pk, transaction.status,
                         old_status))
        return HttpResponse(200, '')
