from django.core.urlresolvers import resolve

from solitude.base import ModelResource
from tastypie import fields
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.validation import FormValidation

from .forms import (SellerValidation, SellerProductValidation,
                    SellerPaypalValidation)
from .models import Seller, SellerProduct, SellerPaypal


class SellerResource(ModelResource):
    paypal = fields.ToOneField('lib.sellers.resources.SellerPaypalResource',
                               'paypal', blank=True, full=True,
                               null=True, readonly=True)

    class Meta(ModelResource.Meta):
        queryset = Seller.objects.all()
        fields = ('uuid',)
        list_allowed_methods = ('post', 'get')
        allowed_methods = ('get',)
        resource_name = 'seller'
        validation = FormValidation(form_class=SellerValidation)
        filtering = {
            'uuid': 'exact',
        }


class SellerPaypalResource(ModelResource):
    seller = fields.ToOneField('lib.sellers.resources.SellerResource',
                               'seller')
    secret = fields.BooleanField(readonly=True, attribute='secret_exists')
    token = fields.BooleanField(readonly=True, attribute='token_exists')

    class Meta(ModelResource.Meta):
        queryset = SellerPaypal.objects.all()
        excludes = ['id']
        list_allowed_methods = ['post']
        allowed_methods = ['get', 'put', 'patch']
        resource_name = 'seller'
        validation = FormValidation(form_class=SellerPaypalValidation)
        filtering = {
            'seller': ALL_WITH_RELATIONS,
        }


class BundleFormValidation(FormValidation):
    """
    A subclass of FormValidation that passes the bundle as the first arg
    to your form class.
    """

    def is_valid(self, bundle, request=None):
        """
        Performs a check on ``bundle.data``to ensure it is valid.

        If the form is valid, an empty list (all valid) will be returned. If
        not, a list of errors will be returned.
        """
        # TODO(Kumar) refactor and merge this with buyers.BuyerResource

        # There are two ways to spot when we should be doing this:
        # 1. When there is a specific resource_pk in the PUT or PATCH.
        # 2. When the request.path resolves to having a pk in it.
        # If either of those match, get_via_uri will do the right thing.
        if 'resource_uri' in bundle.data or 'pk' in resolve(request.path)[2]:
            rsrc = SellerProductResource()
            try:
                bundle.obj = rsrc.get_via_uri(request.path)
            except SellerProduct.DoesNotExist:
                pass
        data = bundle.data

        # Ensure we get a bound Form, regardless of the state of the bundle.
        if data is None:
            data = {}

        form = self.form_class(bundle, data)

        if form.is_valid():
            return {}

        # The data is invalid. Let's collect all the error messages & return
        # them.
        return form.errors


class SellerProductResource(ModelResource):
    seller = fields.ForeignKey('lib.sellers.resources.SellerResource',
                               'seller')

    class Meta(ModelResource.Meta):
        excludes = ['id']
        queryset = SellerProduct.objects.all()
        list_allowed_methods = ['post']
        allowed_methods = ['get', 'put', 'patch']
        resource_name = 'product'
        validation = BundleFormValidation(form_class=SellerProductValidation)
