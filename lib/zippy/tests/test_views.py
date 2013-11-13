import json

from django.core.urlresolvers import reverse
from django.test import Client

from nose.tools import eq_, ok_
from test_utils import RequestFactory, TestCase

from ..views import ProxyView, NoReference


class FakeView(ProxyView):

    def get(self, request, *args, **kwargs):
        raise NoReference


class TestZippyView(TestCase):

    def test_no_reference(self):
        req = RequestFactory().get('/')
        eq_(FakeView().dispatch(req, reference_name='bob',
                                resource_name='sellers').status_code, 404)


class TestAPIView(TestCase):

    def test_no_reference(self):
        req = RequestFactory().get('/')
        with self.settings(ZIPPY_MOCK=False):
            eq_(ProxyView().dispatch(req, reference_name='bob',
                                     resource_name='sellers').status_code, 404)


class TestListViews(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('zippy.api_view',
                           args=['reference', 'sellers'])

    def test_retrieve_sellers_empty(self):
        resp = self.client.get(self.url)
        ok_(resp['Content-Type'].startswith('application/json'))

    def test_create_seller(self):
        uuid = 'zippy-uuid'
        seller = {
            'uuid': uuid,
            'status': 'ACTIVE',
            'name': 'John',
            'email': 'jdoe@example.org',
        }
        resp = self.client.post(self.url, seller)
        seller.update({
            'resource_pk': '1',
            'resource_uri': '/sellers/1',
        })
        eq_(json.loads(resp.content), seller)


class TestItemViews(TestCase):

    def setUp(self):
        self.client = Client()
        self.uuid = 'zippy-uuid'
        self.url_list = reverse('zippy.api_view',
                                args=['reference', 'sellers'])

    def url(self, pk):
        return reverse('zippy.api_view',
                       args=['reference', 'sellers', pk])

    def create_seller(self):
        seller = {
            'uuid': self.uuid,
            'status': 'ACTIVE',
            'name': 'John',
            'email': 'jdoe@example.org',
        }
        self.client.post(self.url_list, seller)
        seller.update({
            'resource_pk': '1',
            'resource_uri': '/sellers/1',
        })
        return seller

    def test_retrieve_seller(self):
        seller = self.create_seller()
        resp = self.client.get(self.url(self.uuid))
        eq_(json.loads(resp.content), seller)
        ok_(resp['Content-Type'].startswith('application/json'))

    def test_update_seller(self):
        seller = self.create_seller()
        new_name = 'Jack'
        resp = self.client.put(self.url(self.uuid),
                               json.dumps({'name': new_name}),
                               content_type='application/json')
        seller.update({ 'name': new_name })
        eq_(json.loads(resp.content), seller)

    def test_delete_seller(self):
        self.create_seller()
        resp = self.client.delete(self.url(self.uuid))
        eq_(resp.status_code, 200)
