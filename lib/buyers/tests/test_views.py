import json

from django.test import TestCase
from django.core.urlresolvers import reverse

from lib.buyers.models import Buyer


class CheckPinTest(TestCase):

    def setUp(self):
        self.url = reverse('check-pin')
        self.uuid = 'a:uuid'
        self.pin = '5678'

    def test_good_pin(self):
        Buyer.objects.create(uuid=self.uuid, pin=self.pin)
        res = self.client.post(self.url,
                            json.dumps({'uuid': self.uuid, 'pin': self.pin}),
                            content_type='application/octet-stream')
        data = json.loads(res.content)
        assert 'valid' in data
        assert data['valid']

    def test_bad_pin(self):
        Buyer.objects.create(uuid=self.uuid, pin=self.pin)
        res = self.client.post(self.url,
                            json.dumps({'uuid': self.uuid, 'pin': 'lame'}),
                            content_type='application/octet-stream')
        data = json.loads(res.content)
        assert 'valid' in data
        assert not data['valid']
