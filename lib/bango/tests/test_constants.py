from ..constants import match, OK, INVALID


def test_constants():
    assert match('OK', OK)
    assert match('INVALID_FOO', INVALID)
    assert not match('INVALID', INVALID)
