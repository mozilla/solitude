from django import forms
from .models import Seller, SellerPaypal, SellerProduct


class SellerValidation(forms.ModelForm):

    class Meta:
        model = Seller


class SellerPaypalValidation(forms.ModelForm):

    class Meta:
        model = SellerPaypal
        exclude = ['seller', 'token', 'secret']


class SellerProductValidation(forms.ModelForm):

    def __init__(self, bundle, *args, **kw):
        super(SellerProductValidation, self).__init__(*args, **kw)
        self.bundle = bundle

    def clean(self):
        external_id = self.data['external_id']
        if self.bundle.obj.pk and external_id == self.bundle.obj.external_id:
            # This is an update to an existing object but the external ID
            # is not getting modified so there's no reason to check it.
            return self.cleaned_data

        from .resources import SellerResource
        if self.bundle.obj.seller_id:
            seller = self.bundle.obj.seller
        else:
            seller = SellerResource().get_via_uri(self.data['seller'])
        # Check for duplicate external_id here manually because the automatic
        # Django check is thwarted by excluding seller. That is, the
        # unique_together constraint is ignored in the form.
        qs = SellerProduct.objects.filter(seller=seller,
                                          external_id=external_id)
        if qs.exists():
            raise forms.ValidationError('EXTERNAL_PRODUCT_ID_IS_NOT_UNIQUE')

        return self.cleaned_data

    class Meta:
        model = SellerProduct
        exclude = ['seller']
