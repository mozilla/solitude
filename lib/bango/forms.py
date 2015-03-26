import codecs
from datetime import datetime, timedelta

from django import forms
from django.conf import settings
from django.db.models import Q
from django.forms.models import model_to_dict

import mobile_codes
from django_statsd.clients import statsd
from lxml import etree

from lib.bango.client import get_client
from lib.bango.constants import (COUNTRIES, CURRENCIES, INVALID_PERSON, OK,
                                 RATINGS, RATINGS_SCHEME,
                                 VAT_NUMBER_DOES_NOT_EXIST)
from lib.bango.utils import verify_sig
from lib.sellers.models import SellerProductBango
from lib.transactions.constants import (PROVIDER_BANGO, STATUS_COMPLETED,
                                        STATUS_RECEIVED, TYPE_PAYMENT,
                                        TYPE_REFUNDS)
from lib.transactions.forms import check_status
from lib.transactions.models import Transaction
from solitude.base import get_object_or_404, log_cef
from solitude.constants import PAYMENT_METHOD_CHOICES
from solitude.fields import ListField, URLField
from solitude.logger import getLogger

log = getLogger('s.bango')


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

    seller = URLField(to='lib.sellers.resources.SellerResource')

    @property
    def bango_data(self):
        result = self.cleaned_data.copy()
        insert = settings.BANGO_INSERT_STAGE
        if insert:  # See bug 919814.
            result['vendorName'] = insert + result['vendorName']
            result['companyName'] = insert + result['companyName']

        del result['seller']
        if settings.BANGO_NOTIFICATION_URL:
            result.update({
                'eventNotificationURL': settings.BANGO_NOTIFICATION_URL,
                'eventNotificationUsername': settings.BANGO_BASIC_AUTH['USER'],
                'eventNotificationPassword':
                    settings.BANGO_BASIC_AUTH['PASSWORD'],
            })
        return result


class SupportEmailForm(forms.Form):
    supportEmailAddress = forms.CharField()

    @property
    def bango_meta(self):
        return {'raise_on': (INVALID_PERSON,),
                'to_field': 'support_person_id',
                'from_field': 'personId',
                'method': 'UpdateSupportEmailAddress'}

    @property
    def bango_data(self):
        return {'emailAddress': self.cleaned_data.get('supportEmailAddress')}


class FinanceEmailForm(forms.Form):
    financeEmailAddress = forms.CharField()

    @property
    def bango_data(self):
        return {'emailAddress': self.cleaned_data.get('financeEmailAddress')}

    @property
    def bango_meta(self):
        return {'raise_on': (INVALID_PERSON,),
                'to_field': 'finance_person_id',
                'from_field': 'personId',
                'method': 'UpdateFinanceEmailAddress'}


class VatNumberForm(forms.Form):
    vatNumber = forms.CharField(required=False)
    _is_delete = False

    def clean_vatNumber(self):
        data = self.cleaned_data.get('vatNumber', '')
        if not data:
            self._is_delete = True
        return data

    @property
    def bango_data(self):
        return {} if self._is_delete else self.cleaned_data.copy()

    @property
    def bango_meta(self):
        if self._is_delete:
            return {'raise_on': (VAT_NUMBER_DOES_NOT_EXIST,),
                    'method': 'DeleteVATNumber'}
        return {'method': 'SetVATNumber'}


class UpdateAddressForm(forms.Form):
    vendorName = forms.CharField()
    address1 = forms.CharField()
    address2 = forms.CharField(required=False)
    addressCity = forms.CharField()
    addressState = forms.CharField()
    addressZipCode = forms.CharField()
    addressPhone = forms.CharField()
    addressFax = forms.CharField(required=False)
    # Note the docs are wrong, its not AddressCountryIso.
    countryIso = forms.CharField()
    homePageURL = forms.CharField(required=False)

    @property
    def bango_data(self):
        return self.cleaned_data.copy()

    @property
    def bango_meta(self):
        return {'method': 'UpdateAddressDetails'}


class CreateBangoNumberForm(forms.Form):
    seller_bango = URLField(to='lib.bango.resources.package.PackageResource')
    seller_product = URLField(to='lib.sellers.resources.SellerProductResource')
    name = forms.CharField(max_length=100)
    # TODO: Expand this bug 814492.
    categoryId = forms.IntegerField()

    @property
    def bango_data(self):
        result = self.cleaned_data.copy()
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

    def clean_seller_product_bango(self):
        res = self.cleaned_data['seller_product_bango']
        if not res.bango_id:
            raise forms.ValidationError('Empty bango_id for: %s' % res.pk)
        return res


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
    user_uuid = forms.CharField()
    icon_url = forms.URLField(required=False)
    application_size = forms.IntegerField(required=False)  # In bytes.

    @property
    def bango_data(self):
        data = super(CreateBillingConfigurationForm, self).bango_data
        data['externalTransactionId'] = data.pop('transaction_uuid')
        # Converting the application size in rounded kilobytes (default = 1).
        application_size = data.get('application_size', 1) or 1
        application_size = long(application_size) / 1024 or 1
        data['application_size'] = int(application_size)
        for k in ['prices']:
            del data[k]

        return data

    def clean_prices(self):
        # Remarkably like a formset, but without the drama.
        prices = self.cleaned_data.get('prices', [])
        results = []
        for price in prices:
            result = PriceForm(price)
            try:
                if not result.is_valid():
                    errors = []
                    for error in result.errors.values():
                        errors.extend(error)
                    raise forms.ValidationError(errors)
            except AttributeError:
                raise forms.ValidationError('Invalid JSON.')
            results.append(result)
        if not results:
            raise forms.ValidationError(self.fields['prices']
                                            .error_messages['required'])
        return results

    def clean_transaction_uuid(self):
        uuid = self.cleaned_data['transaction_uuid']
        if Transaction.objects.filter(~Q(status=STATUS_RECEIVED)
                                      & Q(uuid=uuid)).exists():
            # In this case one will not be created.
            raise forms.ValidationError('Transaction already exists '
                                        'with that uuid: {0}'.format(uuid))
        return uuid


class PriceForm(forms.Form):
    price = forms.DecimalField()
    currency = forms.ChoiceField(choices=([r, r] for r in CURRENCIES.keys()))
    method = forms.ChoiceField(choices=([r, r]
                                        for r in PAYMENT_METHOD_CHOICES))


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
    # Store the actual price paid.
    amount = forms.DecimalField(required=False)
    currency = forms.CharField(required=False)
    # Bango token to use with the token checker service.
    bango_token = forms.CharField(required=True)
    network = forms.CharField(required=False)

    def __init__(self, request, *attr, **kw):
        self._request = request
        super(NotificationForm, self).__init__(*attr, **kw)

    def clean(self):
        cleaned_data = super(NotificationForm, self).clean()
        trans = cleaned_data.get('moz_transaction')
        sig = cleaned_data.get('moz_signature')
        if trans and sig:
            # Both fields were non-empty so check the signature.
            if not verify_sig(sig, trans.uuid):
                log.info(
                    'Signature failed: %s'
                    % cleaned_data.get('billing_config_id'))
                raise forms.ValidationError(
                    'Signature did not match: %s for %s'
                    % (sig, trans.uuid))

        tok = cleaned_data.get('bango_token')
        if settings.CHECK_BANGO_TOKEN and tok:
            self._check_for_tampering(tok, cleaned_data)

        return cleaned_data

    def _check_for_tampering(self, tok, cleaned_data):
        """
        Use the token service to see if any data has been tampered with.
        """
        cli = get_client().client('token_checker')
        with statsd.timer('solitude.bango.request.checktoken'):
            true_data = cli.service.CheckToken(token=tok)
        if true_data.ResponseCode is None:
            # Any None field means the token was invalid.
            # This might happen if someone tampered with Token= itself in the
            # query string or if Bango's server was messed up.
            statsd.incr('solitude.bango.response.checktoken_fail')
            msg = 'Invalid Bango token: {0}'.format(tok)
            log.error(msg)
            raise forms.ValidationError(msg)

        for form_fld, true_attr in (
                ('moz_signature', 'Signature'),
                ('moz_transaction', 'MerchantTransactionId'),
                ('bango_response_code', 'ResponseCode'),
                ('bango_response_message', 'ResponseMessage'),
                ('bango_trans_id', 'BangoTransactionId'),):
            true_val = getattr(true_data, true_attr)
            # Make sure the true value is a str() just like it is on the query
            # string.
            true_val = str(true_val)
            form_val = cleaned_data.get(form_fld)
            # Since moz_transaction is an object, get the real value.
            if form_val and form_fld == 'moz_transaction':
                form_val = form_val.uuid

            if form_val and form_val != true_val:
                msg = ('Bango query string tampered with: field: {field}; '
                       'fake: {fake}; true: {true}'
                       .format(field=form_fld, fake=form_val, true=true_val))
                log_cef(msg, self._request, severity=3)
                log.info(msg)
                log.info('token check response: {true_data}'
                         .format(true_data=true_data))
                # Completely reject the form since it was tampered with.
                raise forms.ValidationError(
                    'Form field {0} has been tampered with. '
                    'True: {1}; fake: {2}'.format(
                        form_fld, true_val, form_val))

    def clean_network(self):
        network = self.cleaned_data['network']
        if not network:
            return network

        try:
            region, carrier = network.split('_')
        except ValueError:
            raise forms.ValidationError('Network {0} not in the Bango format '
                                        'of COUNTRY_NETWORK.'.format(network))
        try:
            mobile_codes.alpha3(region)
        except KeyError:
            raise forms.ValidationError('Invalid country: {0}'.format(region))

        self.cleaned_data['carrier'] = carrier
        self.cleaned_data['region'] = region
        return network

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


class EventForm(forms.Form):
    notification = forms.CharField(required=True)
    username = forms.CharField(required=True)
    password = forms.CharField(required=True)

    def __init__(self, *args, **kw):
        self.request_encoding = (kw.pop('request_encoding') or
                                 settings.DEFAULT_CHARSET)
        super(EventForm, self).__init__(*args, **kw)

    def clean(self):
        username = self.cleaned_data.get('username', '')
        password = self.cleaned_data.get('password', '')
        if (username != settings.BANGO_BASIC_AUTH['USER'] or
                password != settings.BANGO_BASIC_AUTH['PASSWORD']):
            raise forms.ValidationError('Auth incorrect')
        return self.cleaned_data

    def clean_notification(self):
        # Forms are always in Unicode but lxml works better with bytes.
        n = self.cleaned_data['notification'].encode(self.request_encoding)
        notice = strip_bom(n)
        try:
            try:
                data = etree.fromstring(notice)
            except etree.XMLSyntaxError, exc:
                log.error('XML parse error: {0.__class__.__name__}: {0}'
                          .format(exc))
                raise forms.ValidationError('XML parse error')

            action = data.find('eventList/event/action')
            if action is None:  # bool(action) is False, so check against None.
                raise forms.ValidationError('Action is required')

            if action.text != 'PAYMENT':
                raise forms.ValidationError('Action invalid: {0}'
                                            .format(action.text))

            elem = data.find('eventList/event/data')
            if elem is None:
                raise forms.ValidationError('Data is required')

            # Easier to work with a dictionary than etree.
            data = dict([c.values() for c in elem.getchildren()])
            if (not data.get('externalCPTransId') and
                    not data.get('transId')):
                raise forms.ValidationError('externalCPTransId or transId'
                                            'required')

        except Exception, exc:
            log.error('Error with event XML: '
                      '{0.__class__.__name__}: {0} encoded={1} XML={2}'
                      .format(exc, self.request_encoding, repr(notice)))
            raise

        if data.get('status') != OK:
            # Cannot find any other definitions of what state might be.
            raise forms.ValidationError('Unspecified state: {0}'
                                        .format(data.get('status')))

        trans = None
        # Could be done with a Q(), but more long winded to get some logging.
        if data.get('transId'):
            try:
                # This is not guaranteed to exist on the transaction yet.
                # It might be there.
                trans = Transaction.objects.get(uid_support=data['transId'])
            except Transaction.DoesNotExist:
                log.warning('Transaction not found by transId'
                            .format(data['transId']))

        if not trans and data.get('externalCPTransId'):
            try:
                # The UUID field is the external transaction id that we pass to
                # bango. We use this because we might not know the transaction
                # id. The transaction id is sent in the redirect back from
                # Bango, see bug 903567.
                trans = Transaction.objects.get(uuid=data['externalCPTransId'])
            except Transaction.DoesNotExist:
                log.warning('Transaction not found by externalCPTransId'
                            .format(data['externalCPTransId']))

        if not trans:
            raise forms.ValidationError('Transaction not found, aborting.')

        data['new_status'] = {OK: STATUS_COMPLETED}[data['status']]
        old = model_to_dict(trans)
        old['created'] = trans.created
        new = {'status': data['new_status']}
        try:
            check_status(old, new)
        except forms.ValidationError:
            log.warning('Invalid status change to: {0} for transaction: {1}'
                        .format(data['new_status'], trans.pk))
            raise

        # Instead of having to get the Transaction again save it.
        self.cleaned_data['transaction'] = trans
        return data


class SBIForm(forms.Form):
    seller_bango = URLField(to='lib.bango.resources.package.PackageResource')

    @property
    def bango_data(self):
        result = self.cleaned_data.copy()
        result['packageId'] = result['seller_bango'].package_id
        del result['seller_bango']
        return result


class GetLoginTokenForm(forms.Form):
    emailAddress = forms.EmailField(required=True)
    packageId = forms.IntegerField(required=True)
    personId = forms.IntegerField(required=True)


class GetEmailAddressesForm(forms.Form):
    packageId = forms.IntegerField(required=True)


class RefundForm(forms.Form):
    uuid = forms.CharField()
    manual = forms.BooleanField(required=False)

    def clean_uuid(self):
        transaction = get_object_or_404(
            Transaction,
            uuid=self.cleaned_data['uuid'])

        if transaction.provider != PROVIDER_BANGO:
            raise forms.ValidationError('Not a Bango transaction')

        elif transaction.status != STATUS_COMPLETED:
            raise forms.ValidationError('Not completed')

        elif transaction.type != TYPE_PAYMENT:
            raise forms.ValidationError('Not a payment')

        elif transaction.is_refunded():
            raise forms.ValidationError('Already refunded')

        return transaction


class RefundStatusForm(forms.Form):
    uuid = forms.CharField()

    def clean_uuid(self):
        # Rather than just returning a 404, let's help the caller of this API
        # tell them why their transaction is denied.
        transaction = Transaction.objects.get(uuid=self.cleaned_data['uuid'])
        if transaction.type not in TYPE_REFUNDS:
            raise forms.ValidationError('Not a refund')

        return transaction


def strip_bom(data):
    """
    Strip the BOM (byte order mark) from byte string `data`.

    Returns a new byte string.
    """
    for bom in (codecs.BOM_UTF32_BE,
                codecs.BOM_UTF32_LE,
                codecs.BOM_UTF16_BE,
                codecs.BOM_UTF16_LE,
                codecs.BOM_UTF8):
        if data.startswith(bom):
            data = data[len(bom):]
            break
    return data
