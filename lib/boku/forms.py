from django import forms

from lib.boku.constants import CURRENCIES
from lib.transactions.constants import (PROVIDER_BOKU, STATUS_COMPLETED)
from lib.transactions.models import Transaction

from lib.boku import constants
from lib.boku.client import BokuClientMixin
from lib.boku.errors import BokuException
from lib.boku.utils import fix_price
from lib.sellers.models import Seller
from solitude.logger import getLogger

log = getLogger('s.boku')


class BokuForm(forms.Form):
    """
    Boku form fields all have - in them for the field names, which makes them
    hard to process in a Django form. This converts all the - to _.

    It does not check if that causes any conflicts.
    """
    def __init__(self, data=None, files=None, **kwargs):
        data = dict((k.replace('-', '_'), v) for k, v in (data or {}).items())
        super(BokuForm, self).__init__(data=data, files=files, **kwargs)


class EventForm(BokuForm):
    """
    A form to process the data from Boku.

    This filters out the data by filtering out the fields we want.
    """
    action = forms.ChoiceField(choices=(['billingresult', 'billingresult'],))
    amount = forms.DecimalField()
    currency = forms.ChoiceField(choices=([k, k] for k in CURRENCIES.keys()))
    # To be validated against Boku.
    sig = forms.CharField(max_length=255)
    # This is the uuid.
    param = forms.CharField(max_length=100)
    # The transaction id from Boku.
    trx_id = forms.CharField(max_length=50)

    def clean(self):
        cleaned_data = super(EventForm, self).clean()
        # TODO: before going any further check the sig and or verify
        # that this is valid as per. bug 987846.
        try:
            cleaned_data['amount'] = fix_price(cleaned_data['amount'],
                                               cleaned_data['currency'])
        except (KeyError, AssertionError):
            raise forms.ValidationError('Not a valid price {0} or currency {1}'
                                        .format(cleaned_data.get('amount'),
                                                cleaned_data.get('currency')))
        return cleaned_data

    def clean_param(self):
        # This takes the param, verifies that the transaction exists
        # and returns the transaction as the result.
        uuid = self.cleaned_data['param']

        try:
            trans = Transaction.objects.get(uuid=uuid, provider=PROVIDER_BOKU)
        except Transaction.DoesNotExist:
            log.info('Transaction not found: %s' % uuid)
            raise forms.ValidationError('Transaction not found: %s' % uuid)

        if trans.status == STATUS_COMPLETED:
            raise forms.ValidationError(
                'Transaction already completed; uuid={uuid}'
                .format(uuid=trans.uuid))

        return trans


class BokuTransactionForm(BokuClientMixin, forms.Form):
    callback_url = forms.URLField()
    forward_url = forms.URLField()
    country = forms.ChoiceField(choices=constants.COUNTRY_CHOICES)
    product_name = forms.CharField()
    transaction_uuid = forms.CharField()
    currency = forms.ChoiceField(choices=constants.CURRENCIES.items())
    price = forms.DecimalField()
    seller_uuid = forms.ModelChoiceField(
        queryset=Seller.objects.none(),
        to_field_name='uuid'
    )
    user_uuid = forms.CharField()

    def __init__(self, *args, **kw):
        super(BokuTransactionForm, self).__init__(*args, **kw)
        # In Django 1.7, this was causing a lookup problem because the
        # Boku model wasn't loaded in the proxy. This is a quick fix to solve
        # the 1.7 problem.
        self.fields['seller_uuid'].queryset = (
            Seller.objects.filter(boku__isnull=False)
        )

    def start_transaction(self):
        if not hasattr(self, 'cleaned_data'):
            raise Exception(
                'The form must pass validation'
                'before a transaction can be started.'
            )

        return self.boku_client.start_transaction(
            callback_url=self.cleaned_data['callback_url'],
            forward_url=self.cleaned_data['forward_url'],
            external_id=self.cleaned_data['transaction_uuid'],
            consumer_id=self.cleaned_data['user_uuid'],
            product_name=self.cleaned_data['product_name'],
            price=self.cleaned_data['price'],
            currency=self.cleaned_data['currency'],
            service_id=self.cleaned_data['seller_uuid'].boku.service_id,
            country=self.cleaned_data['country'],
        )


class BokuServiceForm(BokuClientMixin, forms.Form):
    service_id = forms.CharField()

    def clean_service_id(self):
        service_id = self.cleaned_data['service_id']
        try:
            self.boku_client.get_service_pricing(service_id=service_id)
        except BokuException, e:
            raise forms.ValidationError(
                'Failed to verify Boku Service ID: '
                '{service_id} {error}'.format(
                    service_id=service_id,
                    error=e.message
                )
            )

        return service_id
