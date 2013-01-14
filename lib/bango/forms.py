from datetime import datetime, timedelta

import commonware.log

from django import forms
from django.conf import settings

from lib.bango.constants import COUNTRIES, CURRENCIES, RATINGS, RATINGS_SCHEME
from lib.bango.utils import verify_sig
from lib.sellers.models import SellerProductBango
from lib.transactions.constants import STATUS_COMPLETED
from lib.transactions.models import Transaction
from solitude.fields import ListField, URLField

log = commonware.log.getLogger('s.bango')


class ProductForm(forms.ModelForm):
    seller_bango = URLField(to='lib.bango.resources.package.PackageResource')
    seller_product = URLField(to='lib.sellers.resources.SellerProductResource')
    name = forms.CharField()
    packageId = forms.IntegerField()

    class Meta:
        model = SellerProductBango
        fields = ('seller_bango', 'seller_product', 'name', 'packageId')


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
    pageTitle = forms.CharField()
    prices = ListField()
    redirect_url_onerror = forms.URLField()
    redirect_url_onsuccess = forms.URLField()
    transaction_uuid = forms.CharField()

    @property
    def bango_data(self):
        data = super(CreateBillingConfigurationForm, self).bango_data
        data['externalTransactionId'] = data.pop('transaction_uuid')
        del data['prices']
        return data

    def clean_prices(self):
        # Remarkably like a formset, but without the drama.
        prices = self.cleaned_data.get('prices', [])
        results = []
        for price in prices:
            result = PriceForm(price)
            try:
                if not result.is_valid():
                    raise forms.ValidationError(result.errors)
            except AttributeError:
                raise forms.ValidationError('Invalid JSON.')
            results.append(result)
        if not results:
            raise forms.ValidationError(self.fields['prices']
                                            .error_messages['required'])
        return results


class PriceForm(forms.Form):
    amount = forms.DecimalField()
    currency = forms.ChoiceField(choices=([r, r] for r in CURRENCIES.keys()))


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


class NotificationForm(forms.Form):
    # This is our own signature of the moz_transaction that we sent to
    # the Billing Config API
    moz_signature = forms.CharField()
    # When passed into the form, this must be a valid transaction_uuid.
    moz_transaction = forms.CharField()
    # This is the Bango billing config ID we created with the API.
    billing_config_id = forms.CharField()
    # These parameters arrive in the query string.
    bango_response_code = forms.CharField()
    bango_response_message = forms.CharField()
    bango_trans_id = forms.CharField()

    def clean(self):
        cleaned_data = super(NotificationForm, self).clean()
        trans = cleaned_data.get('moz_transaction')
        sig = cleaned_data.get('moz_signature')
        if trans and sig:
            # Both fields were non-empty so check the signature.
            if not verify_sig(sig, trans.uuid):
                log.info('Signature failed: %s'
                         % cleaned_data.get('billing_config_id'))
                raise forms.ValidationError(
                        'Signature did not match: %s for %s'
                        % (sig, trans.uuid))
        return cleaned_data

    def clean_moz_transaction(self):
        uuid = self.cleaned_data['moz_transaction']
        billing_id = self.cleaned_data.get('billing_config_id')

        try:
            trans = Transaction.objects.get(uuid=uuid)
        except Transaction.DoesNotExist:
            log.info('Transaction not found: %s' % billing_id)
            raise forms.ValidationError('Transaction not found: %s' % uuid)

        if trans.status == STATUS_COMPLETED:
            raise forms.ValidationError('Transaction completed: %s' % uuid)

        if trans.created < (datetime.now() -
                            timedelta(seconds=settings.TRANSACTION_EXPIRY)):
            log.info('Transaction: %s' % billing_id)
            raise forms.ValidationError('Transaction expired: %s' % uuid)

        return trans
