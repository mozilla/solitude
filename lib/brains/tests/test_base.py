from django.core.exceptions import NON_FIELD_ERRORS
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


def ValidationError():
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


def CreditCardError():
    return ErrorResult(
        'gateway', {
            'errors': {},
            'message': 'Do Not Honor',
            'verification': {
                'status': 'processor_declined',
                'processor_response_code': 'processor-code',
                'processor_response_text': 'processor response',
            },
        }
    )


def InsecureError():
    return ErrorResult(
        'gateway', {
            'errors': {},
            'message': 'Invalid Secure Payment Data',
            'transaction': {
                'amount': 1,
                'tax_amount': 1,
                'status': 'processor_declined',
                'processor_response_code': 'blah-code',
                'processor_response_text': 'blah',
            },
        }
    )


def FraudError():
    return ErrorResult(
        'gateway', {
            'errors': {},
            'message': 'Gateway Rejected: fraud',
            'verification': {
                'status': 'gateway_rejected',
                'gateway_rejection_reason': 'fraud',
                'cvv_response_code': None,
            },
        }
    )


def CVVError():
    return ErrorResult(
        'gateway', {
            'errors': {},
            'message': 'Gateway Rejected: cvv',
            'verification': {
                'status': 'gateway_rejected',
                'gateway_rejection_reason': 'cvv',
                'cvv_response_code': 'N',
            },
        }
    )


class TestBraintreeError(TestCase):

    def setUp(self):
        self.brain = BraintreeFormatter

    def test_validation_errors(self):
        eq_(self.brain(BraintreeResultError(ValidationError())).format(),
            {'braintree': {
                'thing': [
                    {'message': 'message', 'code': 123},
                    {'message': 'else', 'code': 456}
                ]}
             })

    def test_credit_card_error(self):
        eq_(self.brain(BraintreeResultError(CreditCardError())).format(), {
            'braintree': {
                NON_FIELD_ERRORS: [{
                    'message': 'processor response',
                    'code': 'processor-code',
                }]
            }
        })

    def test_other_error(self):
        eq_(self.brain(BraintreeResultError(InsecureError())).format(), {
            'braintree': {
                NON_FIELD_ERRORS: [{
                    'message': 'Invalid Secure Payment Data',
                    'code': 'unknown',
                }]
            }
        })

    def test_fraud_error(self):
        eq_(self.brain(BraintreeResultError(FraudError())).format(), {
            'braintree': {
                NON_FIELD_ERRORS: [{
                    'message': 'Gateway Rejected: fraud',
                    'code': 'fraud',
                }]
            }
        })

    def test_cvv_error(self):
        eq_(self.brain(BraintreeResultError(CVVError())).format(), {
            'braintree': {
                'cvv': [{
                    'message': 'Gateway Rejected: cvv',
                    'code': 'cvv',
                }]
            }
        })
