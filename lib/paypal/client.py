from collections import defaultdict
from decimal import Decimal, InvalidOperation
import hashlib
import re
import urlparse
import uuid

from django.conf import settings
from django.utils.http import urlquote

import commonware.log
from django_statsd.clients import statsd
import requests

from .header import get_auth_header
from .constants import (PAYPAL_PERSONAL, PAYPAL_PERSONAL_LOOKUP,
                        REFUND_OK_STATUSES)
from .errors import errors, AuthError, PaypalDataError, PaypalError
from .urls import urls

log = commonware.log.getLogger('s.paypal')

# The length of time we'll wait for PayPal.
timeout = getattr(settings, 'PAYPAL_TIMEOUT', 10)


class Client(object):

    def uuid(self):
        return hashlib.md5(str(uuid.uuid4())).hexdigest()

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
        """
        out = []
        escape = lambda k, v: '%s=%s' % (k, urlquote(v))
        # This must be sorted for chained payments to work correctly.
        for k, v in sorted(data.items()):
            if isinstance(v, (list, tuple)):
                out.extend([escape('%s(%s)' % (k, x), v_)
                            for x, v_ in enumerate(v)])
            else:
                out.append(escape(k, v))

        return '&'.join(out)

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

    def call(self, service, data):
        """
        Wrapper around calling the requested paypal service using
        data provided. Adds in timing and logging.
        """
        # Lookup the URL given the service.
        url = urls[service]
        with statsd.timer('solitude.paypal.%s' % service):
            log.info('Calling service: %s' % service)
            return self._call(url, data)

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

    def _call(self, url, data, auth_token=None):
        if 'requestEnvelope.errorLanguage' not in data:
            data['requestEnvelope.errorLanguage'] = 'en_US'

        # Figure out the headers using the token.
        headers = self.headers(url, auth_token=auth_token)

        # Warning, a urlencode will not work with chained payments, it must
        # be sorted and the key should not be escaped.
        nvp = self.nvp(data)
        try:
            # This will check certs if settings.PAYPAL_CERT is specified.
            result = requests.post(url, cert=settings.PAYPAL_CERT, data=nvp,
                                   headers=headers, timeout=timeout,
                                   verify=True)
        except AuthError, error:
            log.error('Authentication error: %s' % error)
            raise
        except Exception, error:
            log.error('HTTP Error: %s' % error)
            # We'll log the actual error and then raise a Paypal error.
            # That way all the calling methods only have catch a Paypal error,
            # the fact that there may be say, a http error, is internal to this
            # method.
            raise PaypalError

        response = dict(urlparse.parse_qsl(result.text))

        if 'error(0).errorId' in response:
            id_, msg = (response['error(0).errorId'],
                        response['error(0).message'])
            log.error('Paypal Error (%s): %s' % (id_, msg))
            raise errors.get(id_, PaypalError)(id=id_, paypal_data=data,
                                               message=msg)

        return response

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

    def get_permission_token(self, token, code):
        """
        Send request for permissions token, after user has granted the
        requested permissions via the PayPal page we redirected them to.
        Documentation: http://bit.ly/Mjh51D
        """
        res = self.call('get-permission-token', {'token': token, 'code': code})
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
            'maxAmountPerPayment': 15,
            'maxNumberOfPaymentsPerPeriod': 15,
            'paymentPeriod': 'DAILY',
            'returnUrl': return_url,
            'startingDate': start.strftime('%Y-%m-%d'),
        }
        res = self.call('get-preapproval-key', data)
        return {'key': res['preapprovalKey']}

    def get_pay_key(self, seller_email, amount, ipn_url, cancel_url,
                    return_url, currency='USD', preapproval=None, memo='',
                    uuid=None):
        """
        Gets a payment key, or processes payments with preapproval.
        Documentation: http://bit.ly/vWV525
        """
        assert self.whitelist([return_url, cancel_url, ipn_url])
        data = {
            'actionType': 'PAY',
            'cancelUrl': cancel_url,
            'currencyCode': currency,
            'ipnNotificationUrl': ipn_url,
            'memo': memo,
            'returnUrl': return_url,
            'trackingId': uuid or self.uuid(),
        }
        if preapproval:
            data['preapprovalKey'] = preapproval
        data.update(self.receivers(seller_email, amount, preapproval))
        res = self.call('get-pay-key', data)
        return {'pay_key': res['payKey'],
                'status': res['paymentExecStatus']}

    def check_purchase(self, pay_key):
        """
        Checks when a purchase is complete.
        Documentation: http://bit.ly/K6oNwz
        """
        res = self.call('check-purchase', {'payKey': pay_key})
        return {'status': res['status']}

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
        return self.parse_personal(self.call('get-personal', data))

    def get_personal_advanced(self, token):
        """
        Ask PayPal for basic personal data based on the token.
        Documentation: http://bit.ly/yRYbRx
        """
        keys = ['post_code', 'address_one', 'address_two', 'city', 'state',
                'phone']
        data = {'attributeList.attribute': [PAYPAL_PERSONAL[k] for k in keys]}
        return self.parse_personal(self.call('get-personal', data))

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

        return clean_responses
