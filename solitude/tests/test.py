from hashlib import md5

from django.core.urlresolvers import reverse

from nose.tools import eq_

from lib.buyers.models import Buyer
from solitude.base import APITest


class TestHeaders(APITest):
    api_name = 'generic'

    def test_content_headers_list(self):
        Buyer.objects.create(uuid='sample:uuid')
        res = self.client.get(reverse('generic:buyer-list'))
        assert 'etag' in res._headers

    def test_content_headers_detail(self):
        buyer = Buyer.objects.create(uuid='sample:uuid')
        res = self.client.get(buyer.get_uri())
        assert 'etag' in res._headers
        eq_(md5(str(buyer.etag)).hexdigest(),
            res._headers['etag'][1][1:-1])

    def test_content_headers_etag_get(self):
        buyer = Buyer.objects.create(uuid='sample:uuid')
        etag = md5(str(buyer.etag)).hexdigest()
        res = self.client.get(
            reverse('generic:buyer-list'),
            HTTP_IF_NONE_MATCH=etag)
        eq_(res.status_code, 304)
        res = self.client.get(buyer.get_uri(), HTTP_IF_NONE_MATCH=etag)
        eq_(res.status_code, 304)

    def test_content_headers_etag_put(self):
        buyer = Buyer.objects.create(uuid='sample:uuid', pin='1234')
        res = self.client.get(buyer.get_uri())
        etag = res._headers['etag'][1][1:-1]
        res = self.client.put(buyer.get_uri(),
                              data={'uuid': buyer.uuid,
                                    'pin': '5678'},
                              HTTP_IF_MATCH=etag)
        eq_(res.status_code, 200)
        buyer.save()
        res = self.client.put(buyer.get_uri(),
                              data={'uuid': buyer.uuid,
                                    'pin': '9101'},
                              HTTP_IF_MATCH=etag)
        eq_(res.status_code, 412)
        res = self.client.put(buyer.get_uri(),
                              data={'uuid': buyer.uuid,
                                    'pin': '9101'})
        eq_(res.status_code, 200)

    def test_content_headers_etag_patch(self):
        buyer = Buyer.objects.create(uuid='sample:uuid', pin='1234')
        res = self.client.get(buyer.get_uri())
        etag = res._headers['etag'][1][1:-1]
        res = self.client.patch(buyer.get_uri(),
                                data={'pin': '5678'},
                                HTTP_IF_MATCH=etag)
        eq_(res.status_code, 200)
        buyer.save()
        res = self.client.patch(buyer.get_uri(),
                                data={'pin': '9101'},
                                HTTP_IF_MATCH=etag)
        eq_(res.status_code, 412)
        res = self.client.patch(buyer.get_uri(),
                                data={'pin': '9101'})
        eq_(res.status_code, 200)
