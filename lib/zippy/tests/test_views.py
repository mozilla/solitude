import json

from django.core.urlresolvers import reverse
from django.test import Client, TestCase

from nose.tools import eq_


class TestViews(TestCase):

    def setUp(self):
        self.client = Client()

    def test_retrieve_sellers_empty(self):
        resp = self.client.get(reverse('zippy.api_view',
                                       args=['reference', 'sellers']))
        eq_(json.loads(resp.content), [])
        eq_(resp['Content-Type'], 'application/json')

    def test_create_seller(self):
        seller = {
            'uuid': 'zippy-uuid',
            'status': 'ACTIVE',
            'name': 'John',
            'email': 'jdoe@example.org',
        }
        resp = self.client.post(reverse('zippy.api_view',
                                        args=['reference', 'sellers']),
                                seller)
        seller.update({
            'resource_pk': '1',
            'resource_uri': '/sellers/1',
        })
        eq_(json.loads(resp.content), seller)
