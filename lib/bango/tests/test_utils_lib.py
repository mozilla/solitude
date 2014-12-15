import os
import tempfile

from django import test

from nose.tools import raises

from lib.bango.utils import sign, terms, terms_directory, verify_sig


class TestSigning(test.TestCase):

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


class TestTerms(test.TestCase):

    def setUp(self):
        self.fr = os.path.join(terms_directory, 'fr.html')

    def tearDown(self):
        if os.path.exists(self.fr):
            os.remove(self.fr)

    def test_en(self):
        assert 'Bango Developer Terms' in terms('sbi')

    def test_fr(self):
        with open(self.fr, 'w') as fr:
            fr.write('fr')
        assert 'fr' in terms('sbi', language='fr')

    def test_fallback(self):
        assert 'Bango Developer Terms' in terms('sbi', language='de')
