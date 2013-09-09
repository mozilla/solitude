import json

from django.test import RequestFactory

from nose.tools import eq_
import mock

from solitude.base import BaseResource, APITest
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.resources import Resource
from tastypie.authorization import Authorization


class TestResource(BaseResource, Resource):
    class Meta:
        authorization = Authorization()

    def obj_get_list(self, *args, **kw):
        return []

    def post_list(self, *args, **kw):
        return []


class TestDelay(APITest):

    def get_request(self, method, data=None, async=True, url='/'):
        data = json.dumps(data) if data else {}
        async = {'HTTP_SOLITUDE_ASYNC': 'async'} if async else {}
        mthd = getattr(RequestFactory(), method)
        return mthd(url, content_type='application/json', data=data, **async)

    def test_not_allowed(self):
        with self.assertRaises(ImmediateHttpResponse):
            TestResource().dispatch('list', self.get_request('get'))

    @mock.patch('lib.delayable.tasks.delayable.delay')
    def test_not_delayable(self, delay):
        TestResource().dispatch('list', self.get_request('post', async=False))
        assert not delay.called

    @mock.patch('lib.delayable.tasks.delayable.delay')
    def test_delayable(self, delay):
        TestResource().dispatch('list', self.get_request('post'))
        assert delay.called

    @mock.patch('lib.delayable.tasks.delayable.delay')
    def test_meta(self, delay):
        TestResource().dispatch('list',
                                self.get_request('post', url='/foo?pk=bar'))
        meta = delay.call_args[0][3]
        eq_(meta['QUERY_STRING'], 'pk=bar')
        eq_(meta['REQUEST_METHOD'], 'POST')
        eq_(meta['PATH_INFO'], '/foo')

    @mock.patch('lib.delayable.tasks.delayable.delay')
    def test_result(self, delay):
        res = TestResource().dispatch('list', self.get_request('post'))
        eq_(res.status_code, 202)
        eq_(set(json.loads(res.content).keys()), set(['replay', 'result']))
