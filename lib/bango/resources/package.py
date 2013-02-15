from tastypie import fields
from tastypie.constants import ALL_WITH_RELATIONS

from lib.sellers.models import SellerBango, SellerProductBango
from solitude.base import ModelFormValidation, ModelResource

from cached import BangoResource
from ..client import response_to_dict
from ..constants import INVALID_PERSON, VAT_NUMBER_DOES_NOT_EXIST
from ..errors import BangoFormError
from ..forms import (CreateBangoNumberForm, FinanceEmailForm, PackageForm,
                     ProductForm, SupportEmailForm, UpdateAddressForm,
                     VatNumberForm)


class PackageResource(ModelResource, BangoResource):
    seller = fields.ForeignKey('lib.sellers.resources.SellerResource',
                               'seller')
    full = fields.DictField('full', null=True)

    # TODO: INVALID_EMAIL varies depending upon the call and there's multiple
    # on this resource
    error_lookup = {
        'INVALID_COUNTRYISO': 'countryIso',
        'INVALID_CURRENCYISO': 'currencyIso',
        'INVALID_URL': 'homePageURL',
    }

    class Meta(ModelResource.Meta):
        queryset = SellerBango.objects.filter()
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'patch']
        resource_name = 'package'
        filtering = {
            'seller': ALL_WITH_RELATIONS
        }

    def build_bundle(self, obj=None, data=None, request=None):
        bundle = (super(PackageResource, self)
                  .build_bundle(obj=obj, data=data, request=request))
        if request.method == 'GET':
            data = self.deserialize_body(request)
            if data.get('full'):
                bundle.full = True

        return bundle

    def dehydrate_full(self, bundle):
        if getattr(bundle, 'full', False):
            return response_to_dict(
                self.client('GetPackage',
                    {'packageId': bundle.obj.package_id}))
        return {}

    def obj_create(self, bundle, request, **kw):
        """
        Create a SellerBango record, which just passes the data
        through to Bango and then stores the result here.
        """
        form = PackageForm(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        resp = self.client('CreatePackage', form.bango_data)
        seller_bango = SellerBango.objects.create(
            seller=form.cleaned_data['seller'],
            package_id=resp.packageId,
            admin_person_id=resp.adminPersonId,
            support_person_id=resp.supportPersonId,
            finance_person_id=resp.financePersonId
        )
        bundle.obj = seller_bango
        return bundle

    def obj_update(self, bundle, request, **kw):
        """
        Update the Bango records and then our record. We'll assume that
        any data that is sent in the patch is optional, if ignored, we won't
        update. We also don't know what the old value is, we just assume if
        its there its an update.
        """
        forms = [FinanceEmailForm(bundle.data), SupportEmailForm(bundle.data),
                 UpdateAddressForm(bundle.data), VatNumberForm(bundle.data)]
        for form in forms:
            if not form.is_valid():
                raise self.form_errors(form)

        for form in forms:
            data = form.bango_data
            keys = form.bango_meta
            data['packageId'] = bundle.obj.package_id
            try:
                result = self.client(keys['method'], data,
                                     raise_on=keys.get('raise_on', None))
            except BangoFormError, exc:
                # We don't know the persons email account, we only
                # know that Bango might not like it if its unchanged.
                if exc.id not in (INVALID_PERSON, VAT_NUMBER_DOES_NOT_EXIST):
                    raise
            else:
                if keys.get('to_field'):
                    # Only change the model in some cases.
                    setattr(bundle.obj, keys.get('to_field'),
                            getattr(result, keys.get('from_field')))

        # Finally save the bundle.
        bundle.obj.save()
        return bundle


class BangoProductResource(ModelResource, BangoResource):
    seller_product = fields.ForeignKey(
        'lib.sellers.resources.SellerProductResource', 'seller_product')

    class Meta(ModelResource.Meta):
        queryset = SellerProductBango.objects.filter()
        list_allowed_methods = ['post', 'get']
        allowed_methods = ['get', 'patch']
        resource_name = 'product'
        filtering = {
            'seller_product': ALL_WITH_RELATIONS,
        }
        validation = ModelFormValidation(form_class=ProductForm)

    def obj_create(self, bundle, request, **kw):
        """
        Creates the SellerBangoProduct record by asking bango for a number.
        """
        form = CreateBangoNumberForm(bundle.data)
        if not form.is_valid():
            return self.form_errors(form)

        resp = self.client('CreateBangoNumber', form.bango_data)

        product = SellerProductBango.objects.create(
            seller_bango=form.cleaned_data['seller_bango'],
            seller_product=form.cleaned_data['seller_product'],
            bango_id=resp.bango,
        )
        bundle.obj = product
        return bundle
