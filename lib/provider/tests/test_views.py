import json

from django.http import HttpResponse
from django.test import RequestFactory, TestCase

import mock
from nose.tools import eq_, ok_
from slumber.exceptions import HttpClientError

from ..views import NoReference, ProxyView


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


class TestAPIasProxy(TestCase):

    def setUp(self):
        super(TestAPIasProxy, self).setUp()

        p = mock.patch('lib.provider.client.get_client')
        get_client = p.start()
        self.addCleanup(p.stop)

        self.api = mock.MagicMock()
        store = mock.Mock()
        store._store = {'base_url': 'http://f'}
        self.api.products.get.__self__ = store
        get_client.return_value = mock.Mock(api=self.api)

        self.fake_data = {'foo': 'bar'}

    def request(self, method, url, resource_name, data=''):
        api = getattr(RequestFactory(), method)
        req = api(url, data and json.dumps(data) or '',
                  content_type='application/json')
        res = ProxyView().dispatch(req, reference_name='reference',
                                   resource_name=resource_name)
        res.render()  # Useful to access content later on.
        res.json = json.loads(res.content)
        return res

    def test_proxy_get_params(self):
        self.api.products.get.return_value = {}
        self.request('get', '/reference/products?foo=bar', 'products')
        assert self.api.products.get.called
        result = self.fake_data.copy()
        result.update({'headers': {'x-solitude-service': 'http://f'}})
        eq_(self.api.products.get.call_args[1], result)

    def test_proxy_error_responses(self):
        # Create a scenario where the proxied API raises an HTTP error.
        data = {'error': {'message': 'something not found'}}
        proxy_res = HttpResponse(data,
                                 content_type='application/json',
                                 status=404)
        proxy_res.json = data
        proxy_res.request = RequestFactory().get('http://api/some/endpoint')
        exc = HttpClientError(proxy_res.content, response=proxy_res)
        self.api.products.get.side_effect = exc
        res = self.request('get', '/reference/products?foo=bar', 'products')
        eq_(res.status_code, 404)
        eq_(res.json, {'error_message': 'something not found'})

    def test_unknown_error_responses(self):
        # Create a scenario where the proxied API raises an HTTP error.
        data = {'unknown_error': 'something went wrong'}
        proxy_res = HttpResponse(data,
                                 content_type='application/json',
                                 status=403)
        proxy_res.json = data
        proxy_res.request = RequestFactory().get('http://api/some/endpoint')
        exc = HttpClientError(proxy_res.content, response=proxy_res)
        self.api.products.get.side_effect = exc
        res = self.request('get', '/reference/products?foo=bar', 'products')
        eq_(res.status_code, 403)
        eq_(res.json, {
            u'error_message': {u'unknown_error': u'something went wrong'}
        })

    def test_proxy_routing(self):
        self.api.products.get.return_value = {}
        self.request('get', '/reference/products/fake-pk', 'products')
        assert self.api.products.get.called

    def test_proxy_post(self):
        self.api.products.post.return_value = {}
        self.request('post', '/reference/products/fake-pk', 'products',
                     self.fake_data)
        assert self.api.products.post.called
        eq_(self.api.products.post.call_args[0][0], self.fake_data)

    def test_proxy_put(self):
        self.api.products.put.return_value = {}
        self.request('put', '/reference/products/fake-pk', 'products',
                     self.fake_data)
        assert self.api.products.put.called
        eq_(self.api.products.put.call_args[0][0], self.fake_data)

    def test_proxy_delete(self):
        self.api.products.delete.return_value = {}
        self.request('delete', '/reference/products/fake-pk', 'products')
        assert self.api.products.delete.called

    def test_proxy_resource_uri(self):
        self.api.products.get.return_value = {
            'resource_uri': '/foo/bar',
            'resource_name': 'products',
            'resource_pk': 'foo-bar',
        }
        res = self.request('get', '/reference/products/fake-pk', 'products')
        eq_(res.json['resource_uri'], '/provider/reference/products/foo-bar/')

    def test_proxy_resource_id(self):
        self.api.products.get.return_value = {
            'resource_uri': '/foo/bar',
            'resource_name': 'products',
            'resource_pk': 'foo-bar',
        }
        res = self.request('get', '/reference/products/fake-pk', 'products')
        ok_(not hasattr(res.json, 'resource_pk'))
        eq_(res.json['id'], 'foo-bar')
