from tastypie.api import Api

from .resources import simple
from .resources.billing import CreateBillingConfigurationResource
from .resources.notification import EventResource, NotificationResource
from .resources.package import BangoProductResource, PackageResource
from .resources.refund import RefundResource
from .resources.sbi import SBIResource

bango = Api(api_name='bango')
for lib in (CreateBillingConfigurationResource,
            BangoProductResource,
            PackageResource,
            NotificationResource,
            EventResource,
            RefundResource,
            SBIResource,
            simple.MakePremiumResource,
            simple.UpdateRatingResource,
            simple.CreateBankDetailsResource):
    bango.register(lib())
