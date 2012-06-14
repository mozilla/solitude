from django.conf.urls.defaults import *

from funfactory.monkeypatches import patch
from tastypie.api import Api

from lib.buyers.resources import BuyerResource, BuyerPaypalResource
from lib.paypal.resources.permission import (CheckPermissionResource,
                                             GetPermissionTokenResource,
                                             GetPermissionURLResource)
from lib.paypal.resources.preapproval import PreapprovalResource
from lib.paypal.resources.pay import PayResource
from lib.sellers.resources import SellerResource, SellerPaypalResource

# Generic APIs
api = Api(api_name='generic')
api.register(BuyerResource())
api.register(SellerResource())

# PayPal specific APIs
paypal = Api(api_name='paypal')
paypal.register(BuyerPaypalResource())
paypal.register(PayResource())
paypal.register(PreapprovalResource())
paypal.register(GetPermissionURLResource())
paypal.register(CheckPermissionResource())
paypal.register(GetPermissionTokenResource())
paypal.register(SellerPaypalResource())

patch()
urlpatterns = patterns('',
    url(r'^', include(api.urls)),
    url(r'^', include(paypal.urls)),
    url(r'^$', 'solitude.views.home')
)


handler500 = handler404 = handler403 = 'solitude.views.error'
