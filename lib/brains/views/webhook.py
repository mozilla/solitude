from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.conf import settings

from lib.brains.client import get_client
from lib.brains.forms import WebhookParseForm, WebhookVerifyForm
from solitude.errors import FormError
from solitude.logger import getLogger

log = getLogger('s.brains')
debug_log = getLogger('s.webhook')


def webhook(request):
    if request.method.lower() == 'get':
        return verify(request)
    return parse(request)


@api_view(['POST'])
def parse(request):
    form = WebhookParseForm(request.DATA)
    if not form.is_valid():
        raise FormError(form.errors)

    parsed = get_client().WebhookNotification.parse(*form.braintree_data)
    log.info('Received webhook: {p.kind}.'.format(p=parsed))
    debug_log.debug(parsed)
    # TODO: actually do something with the web hook.
    return Response(status=204)


@api_view(['GET'])
def verify(request):
    form = WebhookVerifyForm(request.QUERY_PARAMS)
    if not form.is_valid():
        raise FormError(form.errors)

    res = get_client().WebhookNotification.verify(form.braintree_data)
    log.info('Received verification response: {r}'.format(r=res))
    return Response(res)
