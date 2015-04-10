from django_statsd.clients import statsd
from rest_framework.decorators import api_view
from rest_framework.response import Response

from lib.bango.constants import CANCEL, OK
from lib.bango.forms import NotificationForm
from lib.bango.views.base import BangoResource
from lib.transactions.constants import (STATUS_CANCELLED, STATUS_COMPLETED,
                                        STATUS_FAILED, STATUSES_INVERTED)
from solitude.base import log_cef
from solitude.logger import getLogger

log = getLogger('s.bango')


@api_view(['POST'])
def notification(request):
    view = BangoResource()
    form = NotificationForm(request, request.DATA)

    bill_conf_id = form.data.get('billing_config_id')
    log.info('Received notification for billing_config_id %r: '
             'bango_response_code: %r; bango_response_message: %r; '
             'bango_trans_id: %r; bango_token: %r; moz_transaction: %r; '
             'amount: %r; currency: %r'
             % (bill_conf_id,
                form.data.get('bango_response_code'),
                form.data.get('bango_response_message'),
                form.data.get('bango_trans_id'),
                form.data.get('bango_token'),
                form.data.get('moz_transaction'),
                form.data.get('amount'),
                form.data.get('currency')))

    if not form.is_valid():
        log.info(u'Notification invalid: %s' % bill_conf_id)
        return view.form_errors(form)

    trans = form.cleaned_data['moz_transaction']
    states = {OK: ['completed', STATUS_COMPLETED],
              CANCEL: ['cancelled', STATUS_CANCELLED]}
    message, state = states.get(form.cleaned_data['bango_response_code'],
                                ['failed', STATUS_FAILED])

    log.info(u'Transaction %s: %s' % (message, trans.uuid))
    statsd.incr('bango.notification.%s' % message)
    statsd.decr('solitude.pending_transactions')

    log_cef('Transaction change success', request, severity=7,
            cs6Label='old', cs6=STATUSES_INVERTED.get(trans.status),
            cs7Label='new', cs7=STATUSES_INVERTED.get(state))

    trans.status = state
    # This is the id for the actual transaction, useful for refunds.
    trans.uid_support = form.cleaned_data['bango_trans_id']
    # The price/currency may be empty for error notifications.
    trans.amount = form.cleaned_data['amount']
    trans.currency = form.cleaned_data['currency']
    # Set carrier and region.
    if form.cleaned_data.get('network'):
        trans.carrier = form.cleaned_data['carrier']
        trans.region = form.cleaned_data['region']

    trans.save()
    return Response(status=204)
