from nose.tools import eq_
import test_utils

from lib.bluevia.forms import PayValidation, JWTValidation
from lib.sellers.tests.utils import make_seller_bluevia
from lib.bluevia.client import get_client

uuid = 'sample:uid'
data = {'amount': '5', 'aud': 'foo.com', 'app_name': 'foo',
        'app_description': 'foo bar', 'chargeback_url': 'http://f.com/cb.url',
        'currency': 'USD', 'postback_url': 'http://f.com/pb.url',
        'product_data': 'something', 'seller': uuid, 'typ': 'foo.com/blargh'}


class TestPayValidation(test_utils.TestCase):

    def setUp(self):
        self.seller, self.bluevia = make_seller_bluevia(uuid)

    def test_seller(self):
        form = PayValidation(data)
        assert form.is_valid(), form.errors
        eq_(form.cleaned_data['id'], 'something')

    def test_no_bluevia(self):
        self.bluevia.delete()
        assert not PayValidation(data).is_valid()

    def test_empty_bluevia(self):
        self.bluevia.bluevia_id = ''
        self.bluevia.save()
        assert not PayValidation(data).is_valid()

    def test_no_seller(self):
        _data = data.copy()
        _data['seller'] = 'foo'
        assert not PayValidation(_data).is_valid()

    def test_not_amount(self):
        _data = data.copy()
        _data['amount'] = 'some spam'
        assert not PayValidation(_data).is_valid()

    def test_type_mismatch(self):
        _data = data.copy()
        _data['typ'] = 'wat'
        assert not PayValidation(_data).is_valid()


class TestJWTValidation(test_utils.TestCase):

    def setUp(self):
        self.seller, self.bluevia = make_seller_bluevia(uuid)

    def test_bogus(self):
        form = JWTValidation({'jwt': 'foo', 'seller': uuid})
        assert not form.is_valid()
        eq_('Not enough segments', form.errors['jwt'][0])

    def test_good(self):
        # TODO: when getting and storing the secret is stored out,
        # this test will need fixing.
        jwt = get_client().create_jwt(id='blarg', secret='some-unknown',
                                      **data)
        form = JWTValidation({'jwt': jwt, 'seller': uuid})
        assert form.is_valid(), form.errors
