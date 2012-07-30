import jwt
from nose.tools import eq_
import test_utils

from lib.bluevia.client import Client


class TestValidation(test_utils.TestCase):

    def setUp(self):
        self.client = Client()

    def test_create_empty(self):
        with self.assertRaises(AssertionError):
            self.client.create_jwt()

    def create(self):
        data = {'amount': '5',
                'app_name': 'foo',
                'app_description': 'foo bar',
                'aud': 'foo',
                'chargeback_url': 'http://foo.com/chargeback.url',
                'currency': 'USD',
                'postback_url': 'http://foo.com/postback.url',
                'product_data': 'something',
                'seller': 'some:uuid',
                'typ': 'foo/bar'}
        return self.client.create_jwt(id='bah', secret='foo', **data)

    def test_decode(self):
        eq_(jwt.decode(self.create(), 'foo')['iss'], 'bah')

    def test_decode_error(self):
        with self.assertRaises(jwt.DecodeError):
            jwt.decode(self.create(), 'oops')
