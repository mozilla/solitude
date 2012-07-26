import logging

from django.conf import settings

from .client import get_client
from .errors import PaypalError

log = logging.getLogger('s.paypal')


class Check(object):
    """
    Run a series of tests on PayPal for either an addon or a paypal_id.
    The add-on is not required, but we'll do another check or two if the
    add-on is there.
    """

    def __init__(self, paypal_id=None, paypal_permissions_token=None,
                 prices=None):
        # If this state flips to False, it means they need to
        # go to Paypal and re-set up permissions. We'll assume the best.
        self.state = {'permissions': True}
        self.tests = ['id', 'refund', 'currencies']
        for test in self.tests:
            # Three states for pass:
            #   None: haven't tried
            #   False: tried but failed
            #   True: tried and passed
            self.state[test] = {'pass': None, 'errors': []}
        self.paypal_id = paypal_id
        self.paypal_permissions_token = paypal_permissions_token
        self.prices = prices
        self.paypal = get_client()

    def all(self):
        self.check_id()
        self.check_refund()
        self.check_currencies()

    def failure(self, test, msg):
        self.state[test]['errors'].append(msg)
        self.state[test]['pass'] = False

    def pass_(self, test):
        self.state[test]['pass'] = True

    def check_id(self):
        """Check that the paypal id is good."""
        test_id = 'id'
        if not self.paypal_id:
            self.failure(test_id, 'No PayPal id provided.')
            return

        try:
            status = self.paypal.get_verified(self.paypal_id)
        except PaypalError:
            self.failure(test_id, 'You do not seem to have a PayPal account.')
            return

        if status['type'] in ['BUSINESS', 'PREMIER']:
            self.pass_(test_id)
            return

        self.failure(test_id, 'You do not have a business or premier account.')

    def check_refund(self):
        """Check that we have the refund permission."""
        test_id = 'refund'
        msg = ('You have not setup permissions for us to check this '
               'paypal account.')

        token = self.paypal_permissions_token
        if not token:
            self.state['permissions'] = False
            self.failure(test_id, msg)
            return

        try:
            status = self.paypal.check_permission(token, ['REFUND'])
            if not status:
                self.state['permissions'] = False
                self.failure(test_id, 'No permission to do refunds.')
            else:
                self.pass_(test_id)
        except PaypalError:
            self.state['permissions'] = False
            self.failure(test_id, msg)
            log.info('Refund permission check returned an error '
                     'for %s' % id, exc_info=True)

    def check_currencies(self):
        """Check that we've got the currencies."""
        test_id = 'currencies'
        if not self.prices:
            self.failure(test_id, 'No prices specified.')
            return

        for currency, amount in self.prices:
            try:
                self.test_paykey({'currency': currency,
                                  'amount': amount,
                                  'email': self.paypal_id})
                log.info('Get paykey passed in %s' % currency)
            except PaypalError:
                msg = 'Failed to make a test transaction in %s.' % (currency)
                self.failure(test_id, msg)
                log.info('Get paykey returned an error '
                         'in %s' % currency, exc_info=True)

        # If we haven't failed anything by this point, it's all good.
        if self.state[test_id]['pass'] is None:
            self.pass_(test_id)

    def test_paykey(self, data):
        """
        Wraps get_paykey filling none optional data with test data. This
        should never ever be used for real purchases.

        The only things that you can set on this are:
        email: who the money is going to (required)
        amount: the amount of money (required)
        currency: valid paypal currency, defaults to USD (optional)
        """
        try:
            fake_url = settings.PAYPAL_URL_WHITELIST[0]
        except IndexError:
            log.error('PAYPAL_URL_WHITELIST must contain a URL.')
            raise
        return self.paypal.get_pay_key(data['email'], data['amount'],
                                       fake_url, fake_url, fake_url,
                                       currency=data['currency'], memo='test')

    @property
    def passed(self):
        """Returns a boolean to check that all the attempted tests passed."""
        values = [self.state[k] for k in self.tests]
        passes = [s['pass'] for s in values if s['pass'] is not None]
        if passes:
            return all(passes)
        return False

    @property
    def errors(self):
        errs = []
        for k in self.tests:
            if self.state[k]['pass'] is False:
                for err in self.state[k]['errors']:
                    errs.append(err)
        return errs
