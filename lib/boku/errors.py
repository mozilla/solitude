class BokuException(Exception):

    def __init__(self, message, result_code=None, result_msg=None,
                 status=None):
        super(BokuException, self).__init__(message)
        self.result_code = result_code
        self.result_msg = result_msg
        self.status = status


class VerificationError(BokuException):

    """Boku failed to verify the transaction."""


class SignatureError(BokuException):

    """Boku failed to provide a valid signature."""
