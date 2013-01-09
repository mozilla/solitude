from tastypie.api import Api

from .resources import simple
from .resources.billing import (CreateBillingConfigurationResource,
                                PaymentNoticeResource)
from .resources.package import BangoProductResource, PackageResource


bango = Api(api_name='bango')
for lib in (CreateBillingConfigurationResource,
            BangoProductResource,
            PackageResource,
            PaymentNoticeResource,
            simple.MakePremiumResource,
            simple.UpdateRatingResource,
            simple.CreateBankDetailsResource):
    bango.register(lib())
