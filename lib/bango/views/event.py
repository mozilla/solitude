from rest_framework.decorators import api_view
from rest_framework.response import Response

from lib.bango.forms import EventForm
from lib.bango.views.base import BangoResource
from lib.transactions.constants import STATUSES_INVERTED
from solitude.base import log_cef
from solitude.logger import getLogger

log = getLogger('s.bango')


@api_view(['POST'])
def event(request):
    view = BangoResource()
    form = EventForm(request.DATA, request_encoding=request.encoding)
    if not form.is_valid():
        log.info('Event invalid.')
        return view.form_errors(form)

    notification = form.cleaned_data['notification']
    transaction = form.cleaned_data['transaction']

    if notification['new_status'] != transaction.status:
        old_status = transaction.status
        transaction.status = notification['new_status']
        transaction.save()

        log_cef('Transaction change success', request, severity=7,
                cs6Label='old', cs6=STATUSES_INVERTED[old_status],
                cs7Label='new', cs7=STATUSES_INVERTED[transaction.status])
        log.info('Transaction {0} changed to {1} from {2}'
                 .format(transaction.pk, transaction.status,
                         old_status))

    return Response(status=204)
