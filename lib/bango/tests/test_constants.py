from ..constants import INVALID, match, OK


def test_constants():
    assert match('OK', OK)
    assert match('INVALID_FOO', INVALID)
    assert not match('INVALID', INVALID)
