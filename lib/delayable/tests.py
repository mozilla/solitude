import json

import mock
from nose.tools import eq_

from models import Delayable
from solitude.base import APITest
from lib.delayable.tasks import delayable


class TestDelay(APITest):

    def setUp(self):
        self.delay = Delayable.objects.create()
        self.result_url = '/delay/result/%s/' % self.delay.uuid
        self.replay_url = '/delay/replay/%s/' % self.delay.uuid

    def test_resource(self):
        res = self.client.get(self.result_url)
        data = json.loads(res.content)
        eq_(data['uuid'], self.delay.uuid, res.content)

    def test_not_there(self):
        self.delay.delete()
        eq_(self.client.get(self.replay_url).status_code, 404)

    def test_status(self):
        self.delay.status_code = '200'
        self.delay.save()
        eq_(self.client.get(self.replay_url).status_code, 200)

    def test_delayable(self):
        res = self.client.get(self.replay_url)
        eq_(res.status_code, 202)
        eq_(res['Solitude-Async'], 'no')

    def test_replayed(self):
        self.delay.run = True
        self.delay.save()
        res = self.client.get(self.replay_url)
        eq_(res.status_code, 202)
        eq_(res['Solitude-Async'], 'yes')

    def test_content(self):
        self.delay.content = 'abc'
        self.delay.save()
        eq_(self.client.get(self.replay_url).content, 'abc')


class TestTask(APITest):

    @mock.patch('solitude.base.TastypieBaseResource.dispatch')
    def test_dispatch(self, dispatch):
        obj = mock.Mock()
        obj.status_code = 202
        obj.content = 'foo'
        dispatch.return_value = obj
        res = delayable('solitude.tests.test_delay', 'TestResource', 'list',
                        {'REQUEST_METHOD': 'POST', 'PATH_INFO': '/'}, '', {},
                        'uid')
        eq_(res.run, True)
        eq_(res.content, 'foo')


class TestDelayableBuyer(APITest):

    def test_buyer(self):
        # A slow end-to-end test.
        res = self.client.post('/generic/buyer/', data={'uuid': 'some:uid'},
                               HTTP_SOLITUDE_ASYNC='yes')
        eq_(res.status_code, 202)
        res_data = json.loads(res.content)

        res = self.client.get(res_data['result'])
        data = json.loads(res.content)
        eq_(res.status_code, 200)
        eq_(data['run'], True)
        eq_(data['status_code'], 201)

        res = self.client.get(res_data['replay'])
        data = json.loads(res.content)
        eq_(res.status_code, 201)
        eq_(data['uuid'], 'some:uid')
