from django.http import HttpResponse

from rest_framework import viewsets

from lib.boku.utils import verify
from lib.boku.forms import EventForm
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

        # Verify this against Boku, this will raise errors if there's
        # an issue.
        verify(transaction, cleaned['amount'], cleaned['currency'])

        old_status = transaction.status
        # For the moment assume that all notifications that come in
        # are complete.
        transaction.status = STATUS_COMPLETED
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
