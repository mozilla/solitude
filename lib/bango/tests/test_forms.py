from unittest import TestCase

from django import forms
from nose.tools import raises

from lib.sellers.resources import SellerResource
from ..forms import URLField


class TestURLField(TestCase):

    def test_valid(self):
        self.field = URLField(to='lib.sellers.resources.SellerResource')
        assert isinstance(self.field.to_instance(), SellerResource)

    @raises(ValueError)
    def test_nope(self):
        self.field = URLField(to='lib.sellers.resources.Nope')
        assert isinstance(self.field.to_instance(), SellerResource)

    @raises(ValueError)
    def test_module(self):
        self.field = URLField(to='lib.nope')
        assert isinstance(self.field.to_instance(), SellerResource)

    @raises(ValueError)
    def test_more_module(self):
        self.field = URLField(to='nope')
        assert isinstance(self.field.to_instance(), SellerResource)

    @raises(forms.ValidationError)
    def test_not_there(self):
        self.field = URLField(to='lib.sellers.resources.SellerResource')
        self.field.clean('/generic/seller/1/')

    @raises(forms.ValidationError)
    def test_not_found(self):
        self.field = URLField(to='lib.sellers.resources.SellerResource')
        self.field.clean('/blarg/blarg/1/')
