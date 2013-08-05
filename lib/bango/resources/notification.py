from django_statsd.clients import statsd

from cached import Resource
from lib.bango.constants import CANCEL, OK
from lib.bango.forms import EventForm, NotificationForm
from lib.transactions.constants import (STATUS_CANCELLED, STATUS_COMPLETED,
                                        STATUS_FAILED)

from solitude.logger import getLogger

log = getLogger('s.bango')


class NotificationResource(Resource):
    """
    Process a Bango notification.

    See the success URL endpoint in WebPay for an example of the Bango
    query string.
    """

    class Meta(Resource.Meta):
        resource_name = 'notification'
        list_allowed_methods = ['post']

    def obj_create(self, bundle, request, **kwargs):
        form = NotificationForm(bundle.data)
        bill_conf_id = form.data.get('billing_config_id')
        log.info('Received notification for billing_config_id %r: '
                 'bango_response_code: %r; bango_response_message: %r; '
                 'bango_trans_id: %r; moz_transaction: %r'
                 % (bill_conf_id,
                    form.data.get('bango_response_code'),
                    form.data.get('bango_response_message'),
                    form.data.get('bango_trans_id'),
                    form.data.get('moz_transaction')))

        if not form.is_valid():
            log.info('Notification invalid: %s' % bill_conf_id)
            raise self.form_errors(form)

        trans = form.cleaned_data['moz_transaction']
        states = {OK: ['completed', STATUS_COMPLETED],
                  CANCEL: ['cancelled', STATUS_CANCELLED]}
        message, state = states.get(form.cleaned_data['bango_response_code'],
                                    ['failed', STATUS_FAILED])

        log.info('Transaction %s: %s' % (message, trans.uuid))
        statsd.incr('bango.notification.%s' % message)
        statsd.decr('solitude.pending_transactions')
        trans.status = state
        # This is the id for the actual transaction, useful for refunds.
        trans.uid_support = form.cleaned_data['bango_trans_id']
        # The price/currency may be empty for error notifications.
        trans.amount = form.cleaned_data['amount']
        trans.currency = form.cleaned_data['currency']
        trans.save()
        return bundle


class EventResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'event'
        list_allowed_methods = ['post']

    def obj_create(self, bundle, request, **kwargs):
        form = EventForm(bundle.data, request_encoding=request.encoding)
        if not form.is_valid():
            log.info('Event invalid.')
            raise self.form_errors(form)

        notification = form.cleaned_data['notification']
        transaction = form.cleaned_data['transaction']
        if notification['new_status'] != transaction.status:
            old_status = transaction.status
            transaction.status = notification['new_status']
            transaction.save()
            log.info('Transaction {0} changed to {1} from {2}'
                     .format(transaction.pk, transaction.status,
                             old_status))

        return bundle
