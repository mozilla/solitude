from nose.tools import eq_
import test_utils

from lib.bluevia.forms import PayValidation
from lib.sellers.tests.utils import make_seller_bluevia


class TestValidation(test_utils.TestCase):

    def setUp(self):
        self.uuid = 'sample:uid'
        self.seller, self.bluevia = make_seller_bluevia(self.uuid)

    def get_data(self):
        return {'amount': '5',
                'aud': 'foo.com',
                'app_name': 'foo',
                'app_description': 'foo bar',
                'chargeback_url': 'http://foo.com/chargeback.url',
                'currency': 'USD',
                'postback_url': 'http://foo.com/postback.url',
                'product_data': 'something',
                'seller': self.uuid,
                'typ': 'foo.com/blargh'}

    def test_seller(self):
        form = PayValidation(self.get_data())
        assert form.is_valid()
        eq_(form.cleaned_data['id'], 'something')

    def test_no_bluevia(self):
        self.bluevia.delete()
        assert not PayValidation(self.get_data()).is_valid()

    def test_empty_bluevia(self):
        self.bluevia.bluevia_id = ''
        self.bluevia.save()
        assert not PayValidation(self.get_data()).is_valid()

    def test_no_seller(self):
        data = self.get_data()
        data['seller'] = 'foo'
        assert not PayValidation(data).is_valid()

    def test_not_amount(self):
        data = self.get_data()
        data['amount'] = 'some spam'
        assert not PayValidation(data).is_valid()

    def test_type_mismatch(self):
        data = self.get_data()
        data['typ'] = 'wat'
        assert not PayValidation(data).is_valid()
