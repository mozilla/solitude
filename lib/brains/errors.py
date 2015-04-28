class MockError(Exception):

    """
    An attempt was made to use the mock, without a corresponding entry
    in the mocks dictionary.
    """


class BraintreeResultError(Exception):

    """
    When an error occurs in the result that is not a standard error.
    Raise this error.
    """

    def __init__(self, result):
        self.result = result
