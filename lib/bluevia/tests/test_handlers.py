import json

import jwt
from nose.tools import eq_

from lib.sellers.tests.utils import make_seller_bluevia
from solitude.base import APITest


class TestPayBluevia(APITest):

    def setUp(self):
        self.api_name = 'bluevia'
        self.uuid = 'sample:uid'
        self.seller, self.bluevia = make_seller_bluevia(self.uuid)
        self.list_url = self.get_list_url('prepare-pay')

    def get_data(self):
        return {'amount': '5',
                'app_name': 'foo',
                'app_description': 'foo bar',
                'aud': 'foo',
                'chargeback_url': 'http://foo.com/chargeback.url',
                'currency': 'USD',
                'postback_url': 'http://foo.com/postback.url',
                'product_data': 'something',
                'seller': self.uuid,
                'typ': 'foo/bar'}

    def test_post(self):
        res = self.client.post(self.list_url, data=self.get_data())
        eq_(res.status_code, 201, res.content)
        content = json.loads(res.content)
        jwt_ = jwt.decode(content['jwt'].encode('ascii'), verify=False)
        eq_(jwt_['request']['productData'], 'something')
        eq_(jwt_['iss'], 'something')

    def test_post_missing(self):
        data = self.get_data()
        del data['amount']
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 400)
