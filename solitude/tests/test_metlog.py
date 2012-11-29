import json
import logging

from django.conf import settings
from django.core.signals import got_request_exception

from django_statsd.clients import get_client as statsd_client
from nose.tools import eq_
from raven.contrib.django.models import get_client
from tastypie.exceptions import ImmediateHttpResponse
import mock
import test_utils

from solitude.base import Resource


class TestMetlogLogging(test_utils.TestCase):
    """
    Test that the solitude settings routes all logging.
    """
    def setUp(self):
        self.request = test_utils.RequestFactory().get('/')
        self.resource = Resource()
        settings.METLOG.sender.msgs.clear()

    @mock.patch('metlog.client.MetlogClient.metlog')
    def test_cef(self, mock_metlog):
        """
        Weak check to make sure that the cef message was formatted
        properly.
        """
        self.resource.method_check = mock.Mock()
        with self.assertRaises(ImmediateHttpResponse):
            self.resource.dispatch('POST', self.request, api_name='foo',
                                   resource_name='bar')

        args = mock_metlog.call_args_list[0]

        payload = args[1]['payload']

        assert 'msg=foo:bar' in payload
        assert 'Solitude' in payload

    @mock.patch('metlog.client.MetlogClient.metlog')
    @mock.patch.object(settings, 'STATSD_CLIENT',
                       'django_statsd.clients.moz_metlog')
    def test_statsd(self, mock_metlog):
        """
        Weak test to see we've got statsd messages passed into metlog.
        """
        statsd_client().incr('solitude.test.counter')
        args = mock_metlog.call_args
        eq_(args[0], ('counter', None, None, None, '1',
            {'rate': 1, 'name': 'solitude.test.counter'}))


class TestSentryRouting(test_utils.TestCase):
    def setUp(self):
        settings.METLOG.sender.msgs.clear()
        self.raven = get_client()

    def test_basic(self):
        self.raven.capture('Message', message='foo')
        events = [self.raven.decode(json.loads(msg)['payload'])
                  for msg in settings.METLOG.sender.msgs]
        eq_(len(events), 1)
        event = events.pop(0)
        self.assertTrue('sentry.interfaces.Message' in event)
        message = event['sentry.interfaces.Message']
        eq_(message['message'], 'foo')
        eq_(event['level'], logging.ERROR)
        eq_(event['message'], 'foo')

        # This check is slightly different than the raven-python
        # assertion.  Check for strings instead of datetime.datetime
        # here.
        self.assertTrue(isinstance(event['timestamp'], basestring))

    def test_signal_integration(self):
        try:
            int('hello')
        except:
            got_request_exception.send(sender=self.__class__, request=None)
        else:
            self.fail('Expected an exception.')

        events = [self.raven.decode(json.loads(msg)['payload'])
                  for msg in settings.METLOG.sender.msgs]

        eq_(len(events), 1)
        event = events.pop(0)
        self.assertTrue('sentry.interfaces.Exception' in event)
        exc = event['sentry.interfaces.Exception']
        eq_(exc['type'], 'ValueError')
        eq_(exc['value'], u"invalid literal for int() with base 10: 'hello'")
        eq_(event['level'], logging.ERROR)
        eq_(event['message'],
            u"ValueError: invalid literal for int() with base 10: 'hello'")
        eq_(event['culprit'],
            'solitude.tests.test_metlog.test_signal_integration')
