from django import forms

from lib.boku.constants import CURRENCIES
from lib.transactions.constants import (PROVIDER_BOKU, STATUS_COMPLETED)
from lib.transactions.models import Transaction

from django.utils.translation import ugettext_lazy as _

from lib.boku import constants
from lib.boku.client import BokuClientMixin
from lib.boku.errors import BokuException
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

    This filters out the data by whitelisting out the fields we want.
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
            raise forms.ValidationError('Transaction completed: %s' % uuid)

        return trans


class BokuTransactionForm(BokuClientMixin, forms.Form):
    callback_url = forms.URLField()
    forward_url = forms.URLField()
    country = forms.ChoiceField(choices=constants.COUNTRY_CHOICES)
    transaction_uuid = forms.CharField()
    price = forms.DecimalField()
    seller_uuid = forms.ModelChoiceField(
        queryset=Seller.objects.filter(boku__isnull=False),
        to_field_name='uuid'
    )
    user_uuid = forms.CharField()

    ERROR_BAD_PRICE = _(
        'This price was not found in the available price tiers.'
    )
    ERROR_BOKU_API = _('There was an error communicating with Boku.')

    def clean(self):
        cleaned_data = super(BokuTransactionForm, self).clean()

        if not ('country' in cleaned_data and
                'seller_uuid' in cleaned_data and
                'price' in cleaned_data):
            # Not all fields have validated correctly
            # and we can not validate the price.
            return cleaned_data

        # Retrieve the available price tiers for the selected country.
        try:
            price_rows = self.boku_client.get_price_rows(
                cleaned_data['country']
            )
        except BokuException, e:
            log.error('Boku API error from get_price_rows: {error}'
                      .format(error=e.message))
            raise forms.ValidationError(
                self.ERROR_BOKU_API.format(message=e.message)
            )

        if cleaned_data['price'] not in price_rows:
            log.debug('Posted price {price} was not a valid Boku row '
                      'for country {country}. Choices: {rows}'
                      .format(price=cleaned_data['price'],
                              rows=price_rows,
                              country=cleaned_data['country']))
            raise forms.ValidationError(self.ERROR_BAD_PRICE)

        # Store the retrieved price row in cleaned_data.
        cleaned_data['price_row'] = price_rows[cleaned_data['price']]

        return cleaned_data

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
            price_row=self.cleaned_data['price_row'],
            service_id=self.cleaned_data['seller_uuid'].boku.service_id,
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
