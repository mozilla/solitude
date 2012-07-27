from collections import defaultdict
from decimal import Decimal, InvalidOperation
import hashlib
import re
import urllib
import urlparse
import uuid

from django.conf import settings
from django.utils.http import urlquote

import commonware.log
from django_statsd.clients import statsd
import requests

from .header import get_auth_header
from .constants import (HEADERS_URL, HEADERS_TOKEN, PAYPAL_PERSONAL,
                        PAYPAL_PERSONAL_LOOKUP, REFUND_OK_STATUSES)
from .errors import errors, AuthError, PaypalDataError, PaypalError
from .urls import urls

log = commonware.log.getLogger('s.paypal')

# The length of time we'll wait for PayPal.
timeout = getattr(settings, 'PAYPAL_TIMEOUT', 10)

def get_uuid():
    return hashlib.md5(str(uuid.uuid4())).hexdigest()


class Client(object):

    check_personal_email = True

    def whitelist(self, urls, whitelist=None):
        """
        Ensure that URLs that are sent through to to PayPal are in our
        whitelist and not some nasty site.
        TODO: move this is up to the form.
        """
        whitelist = whitelist or settings.PAYPAL_URL_WHITELIST
        if not whitelist:
            raise ValueError('URL white list is required.')
        for url in urls:
            if not url.startswith(whitelist):
                raise ValueError('URL not in the white list: %s' % url)
        return True

    def nvp(self, data):
        """
        Dumps a dict out into NVP pairs suitable for PayPal to consume.

        Note: a urlencode will not work with chained payments. It must be
        sorted and the key must not be escaped.
        """
        out = []
        escape = lambda k, v: '%s=%s' % (k, urlquote(v))
        for k, v in sorted(data.items()):
            if isinstance(v, (list, tuple)):
                out.extend([escape('%s(%s)' % (k, x), v_)
                            for x, v_ in enumerate(v)])
            else:
                out.append(escape(k, v))

        return '&'.join(out)

    def prepare_data(self, data):
        """Anything else that needs to be done to prepare data for PayPal."""
        if 'requestEnvelope.errorLanguage' not in data:
            data['requestEnvelope.errorLanguage'] = 'en_US'
        return self.nvp(data)

    def receivers(self, seller_email, amount, preapproval, chains=None):
        """
        Split a payment down into multiple receivers using the chains
        passed in.
        """
        chains = chains or settings.PAYPAL_CHAINS
        try:
            remainder = Decimal(str(amount))
        except (UnicodeEncodeError, InvalidOperation), msg:
            raise PaypalDataError(msg)

        result = {}
        for number, chain in enumerate(chains, 1):
            percent, destination = chain
            this = (Decimal(str(float(amount) * (percent / 100.0)))
                    .quantize(Decimal('.01')))
            remainder = remainder - this
            key = 'receiverList.receiver(%s)' % number
            result.update({
                '%s.email' % key: destination,
                '%s.amount' % key: str(this),
                '%s.primary' % key: 'false',
                # This is only done if there is a chained payment. Otherwise
                # it does not need to be set.
                'receiverList.receiver(0).primary': 'true',
                # Mozilla pays the fees, because we've got a special rate.
                'feesPayer': 'SECONDARYONLY'
            })
            if not preapproval:
                result['%s.paymentType' % key] = 'DIGITALGOODS'

        result.update({
            'receiverList.receiver(0).email': seller_email,
            'receiverList.receiver(0).amount': str(amount),
            'receiverList.receiver(0).invoiceID': 'mozilla-%s' % uuid
        })

        # Adding DIGITALGOODS to a pre-approval triggers an error in PayPal.
        if not preapproval:
            result['receiverList.receiver(0).paymentType'] = 'DIGITALGOODS'

        return result

    def call(self, service, data, auth_token=None):
        """
        Wrapper around calling the requested paypal service using
        data provided. Adds in timing and logging.
        """
        # Lookup the URL given the service.
        url = urls[service]
        errs = errors.get(service, errors['default'])

        with statsd.timer('solitude.paypal.%s' % service):
            log.info('Calling service: %s' % service)
            headers = self.headers(url, auth_token=auth_token)
            data = self.prepare_data(data)
            return self._call(url, data, headers, errs, verify=True)

    def headers(self, url, auth_token=None):
        """
        These are the headers we need to make a paypal call.
        """
        auth = settings.PAYPAL_AUTH
        headers = {
            'X-PAYPAL-APPLICATION-ID': settings.PAYPAL_APP_ID,
            'X-PAYPAL-REQUEST-DATA-FORMAT': 'NV',
            'X-PAYPAL-RESPONSE-DATA-FORMAT': 'NV',
        }

        if auth_token:
            ts, sig = get_auth_header(auth['USER'], auth['PASSWORD'],
                    auth_token['token'], auth_token['secret'], 'POST', url)
            headers['X-PAYPAL-AUTHORIZATION'] = (
                    'timestamp=%s,token=%s,signature=%s' %
                    (ts, auth_token['token'], sig))

        else:
            headers.update({
                'X-PAYPAL-SECURITY-USERID': auth['USER'],
                'X-PAYPAL-SECURITY-PASSWORD': auth['PASSWORD'],
                'X-PAYPAL-SECURITY-SIGNATURE': auth['SIGNATURE'],
            })

        return headers

    def _call(self, url, data, headers, errs, verify=True):
        try:
            result = requests.post(url, data=data, headers=headers,
                                   verify=verify)
        except AuthError, error:
            log.error('Authentication error: %s' % error)
            raise
        except Exception, error:
            log.error('HTTP Error: %s' % error)
            raise PaypalError

        if result.status_code > 299:
            log.error('HTTP Status: %s' % result.status_code)
            raise PaypalError(message='HTTP Status: %s' % result.status_code)

        response = dict(urlparse.parse_qsl(result.text))
        if 'error(0).errorId' in response:
            raise self.error(response, errs)

        return response

    def error(self, res, errs):
        id_, msg = (res['error(0).errorId'], res['error(0).message'])
        # We want some data to produce a nice error. However
        # we do not want to pass everything back since this will go back in
        # the REST response and that might leak data.
        data = {'currency': res.get('currencyCode')}
        log.error('Paypal Error (%s): %s' % (id_, msg))
        return errs.get(id_, PaypalError)(id=id_, message=msg, data=data)

    def get_permission_url(self, url, scope):
        """
        Send permissions request to PayPal for privileges on
        this PayPal account. Returns URL on PayPal site to visit.
        Documentation: http://bit.ly/zlhXlT
        """
        assert self.whitelist([url])
        res = self.call('request-permission',
                        {'scope': scope, 'callback': url})
        return {'token': urls['grant-permission'] + res['token']}

    def check_permission(self, token, permissions):
        """
        Asks PayPal whether the PayPal ID for this account has granted
        the permissions requested to us. Permissions are strings from the
        PayPal documentation.
        Documentation: http://bit.ly/zlhXlT
        """
        res = self.call('get-permission', {'token': token})
        # In the future we may ask for other permissions so let's just
        # make sure REFUND is one of them.
        result = [v for (k, v) in res.iteritems() if k.startswith('scope')]
        return {'status': set(permissions).issubset(set(result))}

    def get_permission_token(self, token, verifier):
        """
        Send request for permissions token, after user has granted the
        requested permissions via the PayPal page we redirected them to.
        Documentation: http://bit.ly/Mjh51D
        """
        res = self.call('get-permission-token', {'token': token,
                                                 'verifier': verifier})
        return {'token': res['token'], 'secret': res['tokenSecret']}

    def get_preapproval_key(self, start, end, return_url, cancel_url):
        """
        Get a preapproval key from PayPal. If this passes, you get a key that
        you can use in a redirect to PayPal. We will limit the max amount
        per payment and period.
        Documentation: http://bit.ly/Kj6AGQ
        """
        assert self.whitelist([return_url, cancel_url])
        data = {
            'cancelUrl': cancel_url,
            'currencyCode': 'USD',
            'endingDate': end.strftime('%Y-%m-%d'),
            'maxTotalAmountOfAllPayments': '2000',
            'returnUrl': return_url,
            'startingDate': start.strftime('%Y-%m-%d'),
        }
        if settings.PAYPAL_LIMIT_PREAPPROVAL:
            data.update({
                'maxAmountPerPayment': 15,
                'maxNumberOfPaymentsPerPeriod': 15,
                'paymentPeriod': 'DAILY',
            })
        res = self.call('get-preapproval-key', data)
        key = res['preapprovalKey']
        return {'key': key, 'paypal_url': urls['grant-preapproval'] + key}

    def get_pay_key(self, seller_email, amount, ipn_url, cancel_url,
                    return_url, currency='USD', preapproval=None, memo='',
                    uuid=None):
        """
        Gets a payment key, or processes payments with preapproval.
        Documentation: http://bit.ly/vWV525
        """
        assert self.whitelist([return_url, cancel_url, ipn_url])
        uuid = uuid or get_uuid()

        data = {
            'actionType': 'PAY',
            'cancelUrl': cancel_url,
            'currencyCode': currency,
            'ipnNotificationUrl': ipn_url,
            'memo': memo,
            'returnUrl': return_url,
            'trackingId': uuid
        }
        if preapproval:
            data['preapprovalKey'] = preapproval
        data.update(self.receivers(seller_email, amount, preapproval))
        res = self.call('get-pay-key', data)
        return {'pay_key': res['payKey'],
                'status': res['paymentExecStatus'],
                'correlation_id': res['responseEnvelope.correlationId'],
                'uuid': uuid}

    def check_purchase(self, pay_key):
        """
        Checks when a purchase is complete.
        Documentation: http://bit.ly/K6oNwz
        """
        res = self.call('check-purchase', {'payKey': pay_key})
        return {'status': res['status'], 'pay_key': pay_key}

    def parse_personal(self, data):
        result = {}
        for k, v in data.items():
            if k.endswith('personalDataKey'):
                k_ = k.rsplit('.', 1)[0]
                v_ = PAYPAL_PERSONAL_LOOKUP[v]
                result[v_] = data.get(k_ + '.personalDataValue', '')
        return result

    def get_personal_basic(self, token):
        """
        Ask PayPal for basic personal data based on the token.
        Documentation: http://bit.ly/xy5BTs
        """
        keys = ['first_name', 'last_name', 'email', 'full_name',
                'company', 'country', 'payerID']
        data = {'attributeList.attribute': [PAYPAL_PERSONAL[k] for k in keys]}
        return self.parse_personal(self.call('get-personal', data,
                                             auth_token=token))

    def get_personal_advanced(self, token):
        """
        Ask PayPal for basic personal data based on the token.
        Documentation: http://bit.ly/yRYbRx
        """
        keys = ['post_code', 'address_one', 'address_two', 'city', 'state',
                'phone']
        data = {'attributeList.attribute': [PAYPAL_PERSONAL[k] for k in keys]}
        return self.parse_personal(self.call('get-personal-advanced', data,
                                             auth_token=token))

    def parse_refund(self, res):
        responses = defaultdict(lambda: defaultdict(dict))
        for k in sorted(res.keys()):
            group = re.match('refundInfoList.refundInfo\((\d+)\).(.*)', k)
            if group:
                responses[group.group(1)][group.group(2)] = res[k]
        return [responses[k] for k in sorted(responses)]

    def get_refund(self, pay_key):
        """
        Refund a payment.
        Documentation: http://bit.ly/KExwaz
        """
        res = self.parse_refund(self.call('get-refund', {'payKey': pay_key}))
        clean_responses = []
        # TODO (andym): check if this still makes sense.
        for d in res:
            if d['refundStatus'] == 'NOT_PROCESSED':
                # Probably, some other response failed, so PayPal
                # ignored this one.  We'll leave it out of the list we
                # return.
                continue
            if d['refundStatus'] == 'NO_API_ACCESS_TO_RECEIVER':
                # The refund didn't succeed, but let's not raise it as
                # an error, because the caller needs to report this to
                # the user.
                clean_responses.append(d)
                continue
            if d['refundStatus'] not in REFUND_OK_STATUSES:
                raise PaypalError('Bad refund status for %s: %s'
                                  % (d['receiver.email'], d['refundStatus']))
            clean_responses.append(d)

        return {'response': clean_responses}

    def get_verified(self, paypal_id):
        """
        Get the verified status of an account.
        Documentation: http://bit.ly/MPCD2s
        """
        res = self.call('get-verified', {'emailAddress': paypal_id,
                                         'matchCriteria': 'NONE'})
        return {'type': res['userInfo.accountType']}


class ClientProxy(Client):

    def call(self, service, data, auth_token=None):
        """
        When used as a proxy, will send slightly different data
        and log differently.
        """
        errs = errors.get(service, errors['default'])
        with statsd.timer('solitude.proxy.paypal.%s' % service):
            log.info('Calling proxy: %s' % service)
            headers = self.headers(service, auth_token)
            data = self.prepare_data(data)
            return self._call(settings.PAYPAL_PROXY, data, headers,
                              errs, verify=False)

    def headers(self, url, auth_token):
        """
        When being used as a proxy, this will return a set of headers
        that the proxy can understand.
        """
        headers = {HEADERS_URL: url}
        if auth_token:
            headers[HEADERS_TOKEN] = urllib.urlencode(auth_token)
        return headers

gp = 'response.personalData'
rp = 'refundInfoList.refundInfo(0).'
mock_data = {
    'get-verified': {'userInfo.accountType': 'BUSINESS'},
    'get-refund': {},
    'get-personal': {
        gp + '(0).personalDataKey': 'http://axschema.org/contact/country/home',
        gp + '(0).personalDataValue': 'US',
        gp + '(1).personalDataValue': 'batman@gmail.com',
        gp + '(1).personalDataKey': 'http://axschema.org/contact/email',
        gp + '(2).personalDataValue': 'man'
    },
    'get-personal-advanced': {
        gp + '(0).personalDataKey': 'http://schema.openid.net/contact/street1',
        gp + '(0).personalDataValue': '1 Main St',
        gp + '(1).personalDataKey': 'http://schema.openid.net/contact/street2',
        gp + '(2).personalDataValue': 'San Jose',
        gp + '(2).personalDataKey': 'http://axschema.org/contact/city/home'
    },
    'get-permission': {'status': True},
    'get-permission-token': {'token': get_uuid, 'tokenSecret': get_uuid},
    'check-purchase': {'status': 'COMPLETED', 'pay_key': get_uuid},
    'get-pay-key': {
        'paymentExecStatus': 'COMPLETED', 'payKey': get_uuid,
        'responseEnvelope.correlationId': get_uuid},
    'get-preapproval-key': {'preapprovalKey': get_uuid},
    'request-permission': {'token': 'http://mock.solitude.client'},
    'get-refund': {'responses': {
        rp + 'receiver.amount': '123.45',
        rp + 'receiver.email': 'bob@example.com',
        rp + 'refundFeeAmount': '1.03',
        rp + 'refundGrossAmount': '123.45',
        rp + 'refundNetAmount': '122.42',
        rp + 'refundStatus': 'REFUNDED'}
    },
}


class ClientMock(Client):

    check_personal_email = False

    def call(self, service, data, auth_token=None):
        """
        This fakes out the client, by returning fake data in its place.
        TODO: Do something more intelligent with data, eg: returning errors.
        """
        if service in mock_data:
            data = mock_data[service].copy()
            data = dict([(k, '%s:%s' % (k, v()) if callable(v) else v)
                         for k, v in data.iteritems()])
            return data
        raise NotImplementedError(service)

    def get_preapproval_key(self, start, end, return_url, cancel_url):
        """
        We don't want users to have to bounce to PayPal. So we'll fake the
        return url out to return them back to the current site.
        """
        return {'key': 'get-preapproval-key:%s' % get_uuid(),
                'paypal_url': return_url}

    def get_permission_url(self, url, scope):
        """As with get_preapproval_key, skip PayPal."""
        return {'token': url +
                    '&request_token=get-permission-url:%s' % get_uuid() +
                    '&verification_code=get-permission-url:%s' % get_uuid()}


def get_client():
    """
    Use this to get the right client and communicate with PayPal.
    """
    if settings.PAYPAL_MOCK:
        return ClientMock()
    if settings.PAYPAL_PROXY and not settings.SOLITUDE_PROXY:
        return ClientProxy()
    return Client()
