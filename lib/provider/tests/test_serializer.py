from nose.tools import eq_
from rest_framework import serializers

from lib.provider.serializers import Remote
from lib.sellers.models import Seller
from lib.sellers.tests.utils import SellerTest


class Sample(Remote):
    pk = serializers.CharField(max_length=100)
    remote = serializers.CharField(max_length=100)

    class Meta:
        model = Seller
        fields = ['pk']
        remote = ['remote']


class TestSample(SellerTest):

    def test_remote(self):
        eq_(Sample(data={'local': 'f', 'remote': 'b'}).remote_data,
            {'remote': 'b'})

    def test_restore(self):
        seller = self.create_seller()
        eq_(Sample().restore_object({'pk': seller.pk, 'remote': 'b'}).pk,
            seller.pk)
