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

        cc_result = self.error.result.credit_card_verification
        if cc_result:
            log.debug('credit card processing error: {r}'.format(r=cc_result))
            errors[NON_FIELD_ERRORS].append({
                # Prefix the actual error code with `cc-' so that it's sort
                # of namespaced against other types of error codes.
                'code': 'cc-{c}'.format(c=cc_result.processor_response_code),
                'message': cc_result.processor_response_text,
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
