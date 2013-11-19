from django.core.urlresolvers import reverse

from mock import patch
from nose.tools import eq_

from lib.bango.constants import OK
from lib.bango.client import ClientMock
from lib.bango.tests import samples, utils

from solitude.base import APITest

class TestNope(APITest):

    def test(self):
        self.url = reverse('zippy.bango.nope')
        eq_(self.client.get(self.url).status_code, 405)


class TestProduct(APITest):
    uuid = 'sample:uuid'

    def setUp(self):
        self.objs = utils.make_no_product()
        self.url = reverse('zippy.bango.product')

    def get_data(self):
        data = samples.good_bango_number
        data['seller_product'] = self.get_detail_url('product',
            self.objs.product.pk, api_name='generic')
        data['seller_bango'] = self.get_detail_url('package',
            self.objs.bango.pk, api_name='bango')
        return data

    def test(self):
        res = self.client.post(self.url, data=self.get_data())
        eq_(res.status_code, 200, res.json)

    def test_form_fail(self):
        data = self.get_data()
        del data['seller_bango']
        res = self.client.post(self.url, data=data)
        eq_(res.status_code, 400, res.json)

    @patch.object(ClientMock, 'mock_results')
    def test_calls(self, mock_results):
        mock_results.return_value = {'responseCode': OK,
                                     'bango': '1'}
        res = self.client.post(self.url, data=self.get_data())
        eq_(res.status_code, 200, res.json)
        eq_(len(mock_results.call_args_list), 4)
