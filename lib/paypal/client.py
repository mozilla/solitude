import urlparse

from django.conf import settings
from django.utils.http import urlquote

import commonware.log
from django_statsd.clients import statsd
import requests

from .errors import errors, AuthError, PaypalError
from .urls import urls

log = commonware.log.getLogger('s.paypal')

# The length of time we'll wait for PayPal.
timeout = getattr(settings, 'PAYPAL_TIMEOUT', 10)


class Client(object):

    def whitelist(self, urls, whitelist=None):
        """
        Ensure that URLs that are sent through to to PayPal are in our
        whitelist and not some nasty site.
        """
        for url in urls:
            if not url.startswith(whitelist or settings.PAYPAL_URL_WHITELIST):
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

    def call(self, service, paypal_data):
        """
        Wrapper around calling the requested paypal service using
        data provided. Adds in timing and logging.
        """
        # Lookup the URL given the service.
        url = urls[service]
        with statsd.timer('solitude.paypal.%s' % service):
            log.info('Calling service: %s' % service)
            return self._call(url, paypal_data)

    def headers(self):
        """
        These are the headers we need to make a paypal call.
        """
        # TODO (andym): set up the appropriate headers.
        auth = settings.PAYPAL_AUTH
        headers = {}
        for key, value in [
                ('application-id', settings.PAYPAL_APP_ID),
                ('request-data-format', 'NV'),
                ('response-data-format', 'NV'),
                ('security-userid', auth['USER']),
                ('security-password', auth['PASSWORD']),
                ('security-signature', auth['SIGNATURE'])]:
            headers['X-PAYPAL-%s' % key.upper()] = value

        return headers

    def _call(self, url, data):
        if 'requestEnvelope.errorLanguage' not in data:
            data['requestEnvelope.errorLanguage'] = 'en_US'

        headers = self.headers()
        # If we've got a token, we need to auth using the token which uses the
        # paypalx lib. This is primarily for the GetDetails API.
        #if token:
        #   token = dict(urlparse.parse_qsl(token))
        #   ts, sig = get_auth_header(auth['USER'], auth['PASSWORD'],
        #                          token['token'], token['secret'],
        #                          'POST', url)
        #   headers['X-PAYPAL-AUTHORIZATION'] = ('timestamp=%s,token=%s,'
        #                                        'signature=%s' %
        #                                        (ts, token['token'], sig))

        #if ip:
        #    headers['X-PAYPAL-DEVICE-IPADDRESS'] = ip

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
            raise errors.get(id_, PaypalError)(id=id_, paypal_data=data)

        return response

    def get_permission_url(self, url, scope):
        """
        Send permissions request to PayPal for privileges on
        this PayPal account. Returns URL on PayPal site to visit.
        Documentation: http://bit.ly/zlhXlT
        """
        res = self.call('request-permission',
                        {'scope': scope, 'callback': url})
        return urls['grant-permission'] + res['token']

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
        return set(permissions).issubset(set(result))

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
