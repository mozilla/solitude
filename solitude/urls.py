from django.conf import settings
from django.conf.urls.defaults import *

from tastypie.api import Api

from lib.bluevia.urls import bluevia
from lib.buyers.resources import BuyerResource, BuyerPaypalResource
from lib.paypal.urls import paypal
from lib.sellers.resources import (SellerResource, SellerBlueviaResource,
                                   SellerPaypalResource)
from lib.services.resources import (ErrorResource, SettingsResource,
                                    StatusResource)
from lib.transactions.resources import TransactionResource

# Generic APIs
api = Api(api_name='generic')
api.register(BuyerResource())
api.register(SellerResource())

# PayPal specific APIs
paypal.register(BuyerPaypalResource())
paypal.register(SellerPaypalResource())
paypal.register(TransactionResource())

# BlueVia specific APIs
bluevia.register(SellerBlueviaResource())

# Service APIs
service = Api(api_name='services')
service.register(ErrorResource())
if settings.CLEANSED_SETTINGS_ACCESS:
    service.register(SettingsResource())
service.register(StatusResource())

urlpatterns = patterns('',
    url(r'^proxy/paypal/', include('lib.proxy.urls')),
    url(r'^', include(api.urls)),
    url(r'^', include(paypal.urls)),
    url(r'^', include(bluevia.urls)),
    url(r'^', include(service.urls)),
    url(r'^$', 'solitude.views.home')
)

handler500 = handler404 = handler403 = 'solitude.views.error'
