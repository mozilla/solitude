import os
import tempfile

from nose.tools import raises
import test_utils

from lib.bango.utils import sign, verify_sig


class TestSigning(test_utils.TestCase):

    def test_sign(self):
        sig = sign('123')
        assert verify_sig(sig, '123')

    def test_sign_unicode(self):
        sig = sign('123')
        assert verify_sig(sig, u'123')

    @raises(TypeError)
    def test_cannot_sign_non_ascii(self):
        sign(u'Ivan Krsti\u0107')

    def test_wrong_key(self):
        tmp = tempfile.NamedTemporaryFile(mode='w', delete=False)
        tmp.write('some secret')
        tmp.close()
        self.addCleanup(lambda: os.unlink(tmp.name))
        with self.settings(AES_KEYS={'bango:signature': tmp.name}):
            sig = sign('123')
        assert not verify_sig(sig, '123')
