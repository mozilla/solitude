from django.test import TestCase

from nose.tools import eq_
from rest_framework.serializers import Serializer

from lib.brains import serializers


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
