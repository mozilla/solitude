import json

from django.core.urlresolvers import reverse
from django.test import Client

from nose.tools import eq_
from test_utils import RequestFactory, TestCase

from ..views import APIView, NoReference, ZippyView


class FakeView(ZippyView):

    def get(self, request):
        raise NoReference


class TestZippyView(TestCase):

    def test_no_reference(self):
        req = RequestFactory().get('/')
        eq_(FakeView().dispatch(req).status_code, 404)


class TestAPIView(TestCase):

    def setUp(self):
        self.req = RequestFactory().get('/')

    def test_no_reference(self):
        with self.settings(ZIPPY_MOCK=False):
            eq_(APIView().dispatch(self.req, reference_name='bob',
                                   resource_name='sellers').status_code, 404)


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
