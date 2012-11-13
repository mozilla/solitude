from django.conf import settings
from django.conf.urls.defaults import include, patterns, url

from tastypie.api import Api

from lib.bango.urls import bango
from lib.bluevia.urls import bluevia
from lib.buyers.resources import BuyerResource, BuyerPaypalResource
from lib.buyers.views import check_pin
from lib.paypal.urls import paypal
from lib.sellers.resources import (SellerResource, SellerBlueviaResource,
                                   SellerPaypalResource, SellerProductResource)
from lib.services.resources import (ErrorResource, SettingsResource,
                                    StatusResource)
from lib.transactions.resources import TransactionResource

# Generic APIs
api = Api(api_name='generic')
api.register(BuyerResource())
api.register(SellerResource())
api.register(SellerProductResource())

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
    url(r'^', include(bango.urls)),
    url(r'^', include(service.urls)),
    url(r'^buyer/check_pin', check_pin, name='check-pin'),
    url(r'^$', 'solitude.views.home', name='home'),
)

handler500 = handler404 = handler403 = 'solitude.views.error'
