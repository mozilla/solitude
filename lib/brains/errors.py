from collections import defaultdict

from django.core.exceptions import NON_FIELD_ERRORS

from solitude.errors import ErrorFormatter
from solitude.logger import getLogger

log = getLogger('s.brains')


class MockError(Exception):

    """
    An attempt was made to use the mock, without a corresponding entry
    in the mocks dictionary.
    """


class BraintreeFormatter(ErrorFormatter):

    def format(self):
        errors = defaultdict(list)
        for error in self.error.result.errors.deep_errors:
            errors[error.attribute].append({
                'code': error.code,
                'message': error.message
            })

        # If there's not a verification object,
        # there will be a transaction object or neither.
        error = (self.error.result.credit_card_verification
                 or self.error.result.transaction)
        if error:
            log.debug('Processing error: {}'.format(object))

            if error.status.startswith('gateway'):
                field = NON_FIELD_ERRORS
                # I think these are two cases we care about
                # http://bit.ly/1FbxYCE
                if error.cvv_response_code in ['N', 'U']:
                    field = 'cvv'

                errors[field].append({
                    'code': error.gateway_rejection_reason,
                    # There is no matching gateway_rejection_text.
                    'message': self.error.result.message
                })

            # This covers JCB (failed) and all others (processor declined)
            elif error.status.startswith(('processor', 'failed')):
                errors[NON_FIELD_ERRORS].append({
                    'code': error.processor_response_code,
                    'message': error.processor_response_text,
                })

        # If we haven't found anything fall back to grabbing the message
        # at least.
        if not errors:
            errors[NON_FIELD_ERRORS].append({
                'code': 'unknown',
                'message': self.error.result.message
            })

        return {'braintree': dict(errors)}


class BraintreeResultError(Exception):

    """
    When an error occurs in the result that is not a standard error.
    """
    status_code = 422
    formatter = BraintreeFormatter

    def __init__(self, result):
        self.result = result
