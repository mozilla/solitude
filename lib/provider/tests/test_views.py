import json

from django.http import HttpResponse

from curling.lib import HttpClientError
import mock
from nose.tools import eq_
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


class TestAPIasProxy(TestCase):

    def setUp(self):
        super(TestAPIasProxy, self).setUp()

        p = mock.patch('lib.provider.client.get_client')
        get_client = p.start()
        self.addCleanup(p.stop)

        self.api = mock.Mock()
        domain = mock.Mock(api=self.api)
        get_client.return_value = domain

        self.fake_data = {'foo': 'bar'}

    def request(self, method, url, resource_name, data=''):
        api = getattr(RequestFactory(), method)
        req = api(url, data and json.dumps(data) or '',
                  content_type='application/json')
        res = ProxyView().dispatch(req, reference_name='reference',
                                   resource_name=resource_name)
        res.render()  # Useful to access content later on.
        return res

    def test_proxy_get_params(self):
        self.api.products.get.return_value = {}
        self.request('get', '/reference/products?foo=bar', 'products')
        assert self.api.products.get.called
        eq_(self.api.products.get.call_args[1], self.fake_data)

    def test_proxy_error_responses(self):
        # Create a scenario where the proxied API raises an HTTP error.
        data = json.dumps({'error': 'something not found'})
        proxy_res = HttpResponse(data,
                                 content_type='application/json',
                                 status=404)
        proxy_res.json = data
        proxy_res.request = RequestFactory().get('http://api/some/endpoint')
        exc = HttpClientError(proxy_res.content, response=proxy_res)
        self.api.products.get.side_effect = exc
        res = self.request('get', '/reference/products?foo=bar', 'products')
        eq_(res.status_code, 404)

    def test_proxy_routing(self):
        self.api.products.get.return_value = {}
        self.request('get', '/reference/products/fake-uuid', 'products')
        assert self.api.products.get.called

    def test_proxy_post(self):
        self.api.products.post.return_value = {}
        self.request('post', '/reference/products/fake-uuid', 'products',
                     self.fake_data)
        assert self.api.products.post.called
        eq_(self.api.products.post.call_args[0][0], self.fake_data)

    def test_proxy_put(self):
        self.api.products.put.return_value = {}
        self.request('put', '/reference/products/fake-uuid', 'products',
                     self.fake_data)
        assert self.api.products.put.called
        eq_(self.api.products.put.call_args[0][0], self.fake_data)

    def test_proxy_delete(self):
        self.api.products.delete.return_value = {}
        self.request('delete', '/reference/products/fake-uuid', 'products')
        assert self.api.products.delete.called

    def test_proxy_resource_uri(self):
        self.api.products.get.return_value = {
            'resource_uri': '/foo/bar',
            'resource_name': 'products',
            'resource_pk': 'foo-bar',
        }
        res = self.request('get', '/reference/products/fake-uuid', 'products')
        eq_(json.loads(res.content)['resource_uri'],
            '/provider/reference/products/foo-bar/')

