from decimal import Decimal

from django.conf import settings

from cached import Resource

from lib.bango.client import BangoError, get_client
from lib.bango.constants import MICRO_PAYMENT_TYPES, PAYMENT_TYPES
from lib.bango.forms import CreateBillingConfigurationForm
from lib.bango.signals import create
from lib.bango.utils import sign

from lib.transactions.constants import STATUS_FAILED

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

        data = form.bango_data

        create_data = data.copy()
        create_data['transaction_uuid'] = data.pop('externalTransactionId')

        try:
            resp = self.call(form)
        except BangoError:
            log.error('Error on createBillingConfiguration, uuid: %s'
                      % (create_data['transaction_uuid']))
            create.send(sender=self, bundle=bundle, data=create_data,
                        form=form, status=STATUS_FAILED)
            raise

        bundle.data = {'responseCode': resp.responseCode,
                       'responseMessage': resp.responseMessage,
                       'billingConfigurationId': resp.billingConfigurationId}

        log.info('Sending trans uuid %s from Bango config %s'
                 % (create_data['transaction_uuid'],
                    bundle.data['billingConfigurationId']))

        create.send(sender=self, bundle=bundle, data=create_data, form=form)
        return bundle

    def call(self, form):
        data = form.bango_data
        client = get_client()
        billing = client.client('billing')
        usd_price = None
        price_list = billing.factory.create('ArrayOfPrice')
        for item in form.cleaned_data['prices']:
            price = billing.factory.create('Price')
            price.amount = item.cleaned_data['price']
            price.currency = item.cleaned_data['currency']
            if price.currency == 'USD':
                usd_price = Decimal(price.amount)

            # TODO: remove this.
            # Very temporary and very fragile hack to fix bug 882183.
            # Bango cannot accept regions with price info so if there
            # are two USD values for different regions it triggers a 500 error.
            append = True
            for existing in price_list.Price:
                if existing.currency == price.currency:
                    log.info('Skipping %s:%s because we already have %s:%s'
                             % (price.currency, price.amount,
                                existing.currency, existing.amount))
                    append = False
                    break

            if append:
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
            'APPLICATION_SIZE_KB': data.pop('application_size'),
            # Tell Bango to use our same transaction expiry logic.
            # However, we pad it by 60 seconds to show a prettier Mozilla user
            # error in the case of a real timeout.
            'BILLING_CONFIGURATION_TIME_OUT': settings.TRANSACTION_EXPIRY + 60,
            'REDIRECT_URL_ONSUCCESS': data.pop('redirect_url_onsuccess'),
            'REDIRECT_URL_ONERROR': data.pop('redirect_url_onerror'),
            'REQUEST_SIGNATURE': sign(data['externalTransactionId']),
        }
        user_uuid = data.pop('user_uuid')
        if settings.SEND_USER_ID_TO_BANGO:
            configs['MOZ_USER_ID'] = user_uuid
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
        return self.client('CreateBillingConfiguration', data)
