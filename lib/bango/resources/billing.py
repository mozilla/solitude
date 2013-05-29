from decimal import Decimal

from django.conf import settings

from cached import Resource
from lib.bango.client import get_client
from lib.bango.constants import MICRO_PAYMENT_TYPES, PAYMENT_TYPES
from lib.bango.forms import CreateBillingConfigurationForm
from lib.bango.signals import create
from lib.bango.utils import sign

from solitude.logger import getLogger

log = getLogger('s.bango')


class CreateBillingConfigurationResource(Resource):
    """
    Call the Bango API to begin a payment transaction.

    The resulting billingConfigId can be used on the query
    string in a URL to initiate a user payment flow.

    We are able to configure a few parameters that come
    back to us on the Bango success URL query string.
    Here are some highlights:

    **config[REQUEST_SIGNATURE]**
        This arrives as **MozSignature** in the redirect query string.

    **externalTransactionId**
        This is set to solitude's own transaction_uuid. It arrives
        in the redirect query string as **MerchantTransactionId**.
    """

    class Meta(Resource.Meta):
        resource_name = 'billing'
        list_allowed_methods = ['post']

    def obj_create(self, bundle, request, **kwargs):
        form = CreateBillingConfigurationForm(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        client = get_client()
        billing = client.client('billing')
        data = form.bango_data

        usd_price = None
        price_list = billing.factory.create('ArrayOfPrice')
        for item in form.cleaned_data['prices']:
            price = billing.factory.create('Price')
            price.amount = item.cleaned_data['amount']
            price.currency = item.cleaned_data['currency']
            if price.currency == 'USD':
                usd_price = Decimal(price.amount)
            price_list.Price.append(price)

        data['priceList'] = price_list

        if not usd_price:
            # This should never happen because USD is always part of the list.
            raise ValueError('Purchase for %r did not contain a USD price'
                             % data.get('externalTransactionId'))
        if usd_price < settings.BANGO_MAX_MICRO_AMOUNT:
            type_filters = MICRO_PAYMENT_TYPES
        else:
            type_filters = PAYMENT_TYPES

        types = billing.factory.create('ArrayOfString')
        for f in type_filters:
            types.string.append(f)
        data['typeFilter'] = types

        config = billing.factory.create('ArrayOfBillingConfigurationOption')
        configs = {
            'APPLICATION_CATEGORY_ID': '18',
            'APPLICATION_SIZE_KB': 2,
            'BILLING_CONFIGURATION_TIME_OUT': 120,
            'REDIRECT_URL_ONSUCCESS': data.pop('redirect_url_onsuccess'),
            'REDIRECT_URL_ONERROR': data.pop('redirect_url_onerror'),
            'REQUEST_SIGNATURE': sign(data['externalTransactionId']),
        }
        if settings.BANGO_ICON_URLS:
            icon_url = data.pop('icon_url', None)
            if icon_url:
                configs['APPLICATION_LOGO_URL'] = icon_url

        for k, v in configs.items():
            opt = billing.factory.create('BillingConfigurationOption')
            opt.configurationOptionName = k
            opt.configurationOptionValue = v
            config.BillingConfigurationOption.append(opt)

        data['configurationOptions'] = config
        resp = self.client('CreateBillingConfiguration', data)
        bundle.data = {'responseCode': resp.responseCode,
                       'responseMessage': resp.responseMessage,
                       'billingConfigurationId': resp.billingConfigurationId}

        create_data = data.copy()
        create_data['transaction_uuid'] = data.pop('externalTransactionId')
        create.send(sender=self, bundle=bundle, data=create_data, form=form)
        return bundle
