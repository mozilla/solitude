from collections import defaultdict

from solitude.errors import ErrorFormatter


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

        return {'braintree': dict(errors)}


class BraintreeResultError(Exception):

    """
    When an error occurs in the result that is not a standard error.
    Raise this error.
    """
    status_code = 422
    formatter = BraintreeFormatter

    def __init__(self, result):
        self.result = result
