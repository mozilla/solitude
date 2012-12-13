from cached import Resource

from lib.bango.client import get_client
from lib.bango.forms import CreateBillingConfigurationForm
from lib.bango.signals import create


class CreateBillingConfigurationResource(Resource):

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
        price = billing.factory.create('Price')
        price.amount = data.pop('price_amount')
        price.currency = data.pop('price_currency')
        data['priceList'] = [price]

        config = billing.factory.create('ArrayOfBillingConfigurationOption')
        configs = {
            'APPLICATION_CATEGORY_ID': '18',
            'APPLICATION_SIZE_KB': 2,
            'BILLING_CONFIGURATION_TIME_OUT': 120
        }
        for k, v in configs.items():
            opt = billing.factory.create('BillingConfigurationOption')
            opt.configurationOptionName = k
            opt.configurationOptionValue = v
            config.BillingConfigurationOption.append(opt)

        data['configurationOptions'] = config
        resp = get_client().CreateBillingConfiguration(data)
        bundle.data = {'responseCode': resp.responseCode,
                       'responseMessage': resp.responseMessage,
                       'billingConfigurationId': resp.billingConfigurationId}
        create.send(sender=self, bundle=bundle, data=data, form=form)
        return bundle
