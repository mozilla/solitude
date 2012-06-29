from django.conf import settings
from django.conf.urls.defaults import *

from funfactory.monkeypatches import patch
from tastypie.api import Api

from lib.buyers.resources import BuyerResource, BuyerPaypalResource
from lib.paypal.resources.ipn import IPNResource
from lib.paypal.resources.permission import (CheckPermissionResource,
                                             GetPermissionTokenResource,
                                             GetPermissionURLResource)
from lib.paypal.resources.personal import (CheckPersonalBasic,
                                           CheckPersonalAdvanced)
from lib.paypal.resources.preapproval import PreapprovalResource
from lib.paypal.resources.pay import (CheckPurchaseResource, PayResource,
                                      RefundResource)
from lib.sellers.resources import SellerResource, SellerPaypalResource

from lib.services.resources import ErrorResource, SettingsResource

# Generic APIs
api = Api(api_name='generic')
api.register(BuyerResource())
api.register(SellerResource())

# PayPal specific APIs
paypal = Api(api_name='paypal')
paypal.register(BuyerPaypalResource())
paypal.register(CheckPurchaseResource())
paypal.register(PayResource())
paypal.register(IPNResource())
paypal.register(PreapprovalResource())
paypal.register(GetPermissionURLResource())
paypal.register(CheckPermissionResource())
paypal.register(GetPermissionTokenResource())
paypal.register(CheckPersonalBasic())
paypal.register(CheckPersonalAdvanced())
paypal.register(RefundResource())
paypal.register(SellerPaypalResource())

# Service APIs
service = Api(api_name='services')
service.register(ErrorResource())
if settings.CLEANSED_SETTINGS_ACCESS:
    service.register(SettingsResource())
# TODO: insert nagios and other services here.

patch()
urlpatterns = patterns('',
    url(r'^', include(api.urls)),
    url(r'^', include(paypal.urls)),
    url(r'^', include(service.urls)),
    url(r'^$', 'solitude.views.home')
)


handler500 = handler404 = handler403 = 'solitude.views.error'
