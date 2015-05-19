from django.test import TestCase

from braintree.error_result import ErrorResult
from nose.tools import eq_
from rest_framework.serializers import Serializer

from lib.brains import serializers
from lib.brains.errors import BraintreeFormatter, BraintreeResultError


class Fake(Serializer):
    pass


class FakeObject(object):
    id = 'Fake'


class FakeBraintree(serializers.Braintree):
    fields = ['id']


class TestSerializer(TestCase):

    def test_namespaced(self):
        eq_(serializers.Namespaced(Fake(), Fake()).data,
            {'mozilla': {}, 'braintree': {}})

    def test_braintree(self):
        eq_(FakeBraintree(FakeObject()).data,
            {'id': 'Fake'})


def DummyError():
    # Cribbed from braintree_python source: http://bit.ly/1ICYL1M
    errors = {
        'scope': {
            'errors': [
                {'code': 123, 'message': 'message', 'attribute': 'thing'},
                {'code': 456, 'message': 'else', 'attribute': 'thing'}
            ]
        }
    }
    return ErrorResult(
        'gateway',
        {'errors': errors, 'params': 'params', 'message': 'brief description'}
    )


class TestBraintreeError(TestCase):

    def setUp(self):
        self.brain = BraintreeFormatter
        self.error = DummyError()

    def test_format(self):
        eq_(self.brain(BraintreeResultError(self.error)).format(),
            {'braintree': {
                'thing': [
                    {'message': 'message', 'code': 123},
                    {'message': 'else', 'code': 456}
                ]}
             })
