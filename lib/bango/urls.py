from tastypie.api import Api

from .resources.bank import CreateBankDetailsResource
from .resources.billing import CreateBillingConfigurationResource
from .resources.package import BangoProductResource, PackageResource
from .resources.premium import MakePremiumResource
from .resources.rating import UpdateRatingResource


bango = Api(api_name='bango')
for lib in (CreateBankDetailsResource,
            CreateBillingConfigurationResource,
            BangoProductResource,
            MakePremiumResource,
            PackageResource,
            UpdateRatingResource):
    bango.register(lib())
