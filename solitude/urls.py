from django.conf.urls.defaults import *

from funfactory.monkeypatches import patch
from tastypie.api import Api

from lib.buyers.resource import (BuyerResource, BuyerPaypalResource,
                                 PreapprovalResource)

# Generic APIs
api = Api(api_name='generic')
api.register(BuyerResource())

# PayPal specific APIs
paypal = Api(api_name='paypal')
paypal.register(BuyerPaypalResource())
paypal.register(PreapprovalResource())

patch()
urlpatterns = patterns('',
    url(r'^', include(api.urls)),
    url(r'^', include(paypal.urls)),
    url(r'^$', 'solitude.views.home')
)


handler500 = handler404 = handler403 = 'solitude.views.error'
