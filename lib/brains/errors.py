class MissingMockError(Exception):

    """
    An attempt was made to use the mock, without a corresponding entry
    in the mocks dictionary.
    """
