from nose.tools import eq_, ok_
from test_utils import TestCase

from lib.boku.forms import BokuForm, EventForm
from lib.boku.tests.utils import EventTest
from lib.transactions.constants import PROVIDER_BANGO, STATUS_COMPLETED


class TestBokuForm(TestCase):

    def test_convert(self):
        res = BokuForm(data={'f-': 'b'})
        eq_(res.data, {'f_': 'b'})


class TestForm(EventTest):

    def test_action(self):
        form = EventForm(self.sample())
        ok_(form.is_valid(), form.errors)

    def test_wrong_action(self):
        data = self.sample()
        data['action'] = 'foo'
        form = EventForm(data)
        ok_(not form.is_valid(), form.errors)

    def test_not_exist(self):
        data = self.sample()
        data['param'] = 'does-not-exist'
        form = EventForm(data)
        ok_(not form.is_valid(), form.errors)

    def test_wrong_provider(self):
        self.trans.provider = PROVIDER_BANGO
        self.trans.save()
        ok_(not EventForm(self.sample()).is_valid())

    def test_completed(self):
        self.trans.status = STATUS_COMPLETED
        self.trans.save()
        ok_(not EventForm(self.sample()).is_valid())
