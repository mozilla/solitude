from django import forms

from solitude.fields import URLField
from .constants import (COUNTRIES, CURRENCIES, PAYMENT_TYPES, RATINGS,
                        RATINGS_SCHEME)

import uuid


class PackageForm(forms.Form):
    adminEmailAddress = forms.CharField()
    supportEmailAddress = forms.CharField()
    financeEmailAddress = forms.CharField()
    paypalEmailAddress = forms.CharField()
    vendorName = forms.CharField()
    companyName = forms.CharField()
    address1 = forms.CharField()
    address2 = forms.CharField(required=False)
    addressCity = forms.CharField()
    addressState = forms.CharField()
    addressZipCode = forms.CharField()
    addressPhone = forms.CharField()
    addressFax = forms.CharField(required=False)
    vatNumber = forms.CharField(required=False)
    countryIso = forms.CharField()
    currencyIso = forms.CharField()
    homePageURL = forms.CharField(required=False)
    eventNotificationURL = forms.CharField(required=False)
    seller = URLField(to='lib.sellers.resources.SellerResource')

    @property
    def bango_data(self):
        result = self.cleaned_data.copy()
        del result['seller']
        return result


class UpdateForm(forms.Form):
    supportEmailAddress = forms.CharField(required=False)
    financeEmailAddress = forms.CharField(required=False)


class CreateBangoNumberForm(forms.Form):
    seller_bango = URLField(to='lib.bango.resources.package.PackageResource')
    seller_product = URLField(to='lib.sellers.resources.SellerProductResource')
    name = forms.CharField(max_length=100)
    # TODO: Expand this bug 814492.
    categoryId = forms.IntegerField()

    @property
    def bango_data(self):
        result = self.cleaned_data.copy()
        result['applicationSize'] = 1
        result['packageId'] = result['seller_bango'].package_id
        del result['seller_bango']
        del result['seller_product']
        return result


class SellerProductForm(forms.Form):
    # Base class for a form that interacts using the
    # seller_product_bango resource.
    seller_product_bango = URLField(
        to='lib.bango.resources.package.BangoProductResource')

    @property
    def bango_data(self):
        result = self.cleaned_data.copy()
        result['bango'] = result['seller_product_bango'].bango_id
        del result['seller_product_bango']
        return result


class MakePremiumForm(SellerProductForm):
    currencyIso = forms.ChoiceField(choices=([r, r] for r
                                             in CURRENCIES.keys()))
    price = forms.DecimalField()


class UpdateRatingForm(SellerProductForm):
    ratingScheme = forms.ChoiceField(choices=([r, r] for r in RATINGS_SCHEME))
    rating = forms.ChoiceField(choices=([r, r] for r in RATINGS))


class CreateBillingConfigurationForm(SellerProductForm):
    price_amount = forms.DecimalField()
    price_currency = forms.ChoiceField(choices=([r, r] for r
                                                in CURRENCIES.keys()))
    redirect_url_onsuccess = forms.CharField(max_length=200)
    redirect_url_onerror = forms.CharField(max_length=200)
    pageTitle = forms.CharField()

    @property
    def bango_data(self):
        data = super(CreateBillingConfigurationForm, self).bango_data
        data['typeFilter'] = PAYMENT_TYPES
        data['externalTransactionId'] = uuid.uuid4()
        return data


class CreateBankDetailsForm(forms.Form):
    seller_bango = URLField(to='lib.bango.resources.package.PackageResource')
    bankAccountPayeeName = forms.CharField(max_length=50)
    bankAccountNumber = forms.CharField(max_length=20, required=False)
    bankAccountCode = forms.CharField(max_length=20)
    bankAccountIban = forms.CharField(max_length=34, required=False)
    bankName = forms.CharField(max_length=50)
    bankAddress1 = forms.CharField(max_length=50)
    bankAddress2 = forms.CharField(max_length=50, required=False)
    bankAddressCity = forms.CharField(max_length=50, required=False)
    bankAddressState = forms.CharField(max_length=50, required=False)
    bankAddressZipCode = forms.CharField(max_length=50)
    bankAddressIso = forms.ChoiceField(choices=([r, r] for r in COUNTRIES))

    def clean(self):
        if not (self.cleaned_data.get('bankAccountNumber')
                or self.cleaned_data.get('bankAccountIban')):
            raise forms.ValidationError('Need either bankAccountNumber '
                                        'or bankIban')
        return self.cleaned_data

    @property
    def bango_data(self):
        result = self.cleaned_data.copy()
        result['packageId'] = result['seller_bango'].package_id
        del result['seller_bango']
        return result
