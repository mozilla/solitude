import base64

from braintree.util.xml_util import XmlUtil
from braintree.webhook_notification import WebhookNotification
from rest_framework.decorators import api_view
from rest_framework.response import Response

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

    # Parse the gateway without doing a validation on this server.
    # The validation has happened on the solitude-auth server.
    gateway = get_client().Configuration.instantiate().gateway()
    payload = base64.decodestring(form.cleaned_data['bt_payload'])
    attributes = XmlUtil.dict_from_xml(payload)
    parsed = WebhookNotification(gateway, attributes['notification'])

    log.info('Received webhook: {p.kind}.'.format(p=parsed))
    debug_log.debug(parsed)
    # TODO: actually do something with the web hook.
    return Response(status=204)


@api_view(['GET'])
def verify(request):
    form = WebhookVerifyForm(request.QUERY_PARAMS)
    if not form.is_valid():
        raise FormError(form.errors)

    log.info('Received verification response: {r}'.format(r=form.response))
    return Response(form.response)
