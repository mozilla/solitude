from django.conf import settings
from django.conf.urls.defaults import include, patterns, url

from tastypie.api import Api

from lib.bango.urls import bango
from lib.delayable.resources import DelayableResource, ReplayResource
from lib.buyers.resources import (BuyerConfirmPinResource,
                                  BuyerResetPinResource, BuyerPaypalResource,
                                  BuyerResource, BuyerVerifyPinResource)
from lib.paypal.urls import paypal
from lib.sellers.resources import (SellerResource, SellerPaypalResource,
                                   SellerProductResource)
from lib.services.resources import (ErrorResource, SettingsResource,
                                    StatusResource)
from lib.transactions.resources import TransactionResource

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

# Service APIs
service = Api(api_name='services')
service.register(ErrorResource())
if settings.CLEANSED_SETTINGS_ACCESS:
    service.register(SettingsResource())
service.register(StatusResource())

# URLs to query delayed jobs.
delayable = Api(api_name='delay')
delayable.register(DelayableResource())
delayable.register(ReplayResource())

urlpatterns = patterns('',
    url(r'^proxy/', include('lib.proxy.urls')),
    url(r'^', include(api.urls)),
    url(r'^', include(paypal.urls)),
    url(r'^', include(bango.urls)),
    url(r'^', include(service.urls)),
    url(r'^', include(delayable.urls)),
    url(r'^$', 'solitude.views.home', name='home'),
)

handler500 = handler404 = handler403 = 'solitude.views.error'
