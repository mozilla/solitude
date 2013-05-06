from django.conf import settings
from django.conf.urls.defaults import include, patterns, url

from tastypie.api import Api
from tastypie_services.services import (ErrorResource, SettingsResource,
                                        StatusResource)

from lib.bango.urls import bango
from lib.delayable.resources import DelayableResource, ReplayResource
from lib.buyers.resources import (BuyerConfirmPinResource, BuyerPaypalResource,
                                  BuyerResetPinResource, BuyerResource,
                                  BuyerVerifyPinResource)
from lib.paypal.urls import paypal
from lib.sellers.resources import (SellerPaypalResource, SellerProductResource,
                                   SellerResource)
from lib.services.resources import RequestResource
from lib.transactions.resources import TransactionResource

from solitude.base import handle_500

# Generic APIs
api = Api(api_name='generic')
api.register(BuyerResource())
api.register(BuyerConfirmPinResource())
api.register(BuyerVerifyPinResource())
api.register(BuyerResetPinResource())
api.register(SellerResource())
api.register(SellerProductResource())
api.register(TransactionResource())

# PayPal specific APIs
paypal.register(BuyerPaypalResource())
paypal.register(SellerPaypalResource())

# URLs to query delayed jobs.
delayable = Api(api_name='delay')
delayable.register(DelayableResource())
delayable.register(ReplayResource())

services = Api(api_name='services')
services.register(ErrorResource(set_handler=handle_500))
if getattr(settings, 'CLEANSED_SETTINGS_ACCESS', False):
    services.register(SettingsResource())
services.register(StatusResource(set_handler=handle_500))
services.register(RequestResource())

urlpatterns = patterns('',
    url(r'^proxy/', include('lib.proxy.urls')),
    url(r'^', include(api.urls)),
    url(r'^', include(paypal.urls)),
    url(r'^', include(bango.urls)),
    url(r'^', include(delayable.urls)),
    url(r'^$', 'solitude.views.home', name='home'),
    url(r'^', include(services.urls)),
)

handler500 = 'solitude.views.error'
handler404 = 'solitude.views.error_404'
handler403 = 'solitude.views.error_403'
