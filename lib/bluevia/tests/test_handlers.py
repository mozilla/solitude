import json

import jwt
from nose.tools import eq_

from lib.bluevia.client import get_client
from lib.sellers.tests.utils import make_seller_bluevia
from solitude.base import APITest

uuid = 'sample.uid'
data = {'amount': '5', 'app_name': 'foo', 'app_description': 'foo bar',
        'aud': 'foo', 'chargeback_url': 'http://f.co/cb', 'currency': 'USD',
        'postback_url': 'http://f.co/pb', 'product_data': 'something',
        'seller': uuid, 'typ': 'foo/bar'}


class TestPayBluevia(APITest):

    def setUp(self):
        self.api_name = 'bluevia'
        self.seller, self.bluevia = make_seller_bluevia(uuid)
        self.list_url = self.get_list_url('prepare-pay')

    def test_post(self):
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 201, res.content)
        content = json.loads(res.content)
        jwt_ = jwt.decode(content['jwt'].encode('ascii'), verify=False)
        eq_(jwt_['request']['productData'], 'something')
        eq_(jwt_['iss'], 'something')

    def test_post_missing(self):
        _data = data.copy()
        del _data['amount']
        res = self.client.post(self.list_url, data=_data)
        eq_(res.status_code, 400)


class TestVerifyBluevia(APITest):

    def setUp(self):
        self.api_name = 'bluevia'
        self.seller, self.bluevia = make_seller_bluevia(uuid)
        self.list_url = self.get_list_url('verify-jwt')
        # TODO: when we get the developer secret, this will need fixing
        self.valid = get_client().create_jwt(id='foo', secret='some-unknown',
                                             **data)

    def test_post(self):
        res = self.client.post(self.list_url, data={'jwt': self.valid,
                                                    'seller': uuid})
        eq_(res.status_code, 201, res.content)
        content = json.loads(res.content)
        eq_(content['valid'], True)

    def test_fail(self):
        valid = self.valid[:-2] + 'xx'
        res = self.client.post(self.list_url, data={'jwt': valid,
                                                    'seller': uuid})
        eq_(res.status_code, 400, res.content)
        eq_(self.get_errors(res.content, 'jwt')[0],
            'Signature verification failed')
