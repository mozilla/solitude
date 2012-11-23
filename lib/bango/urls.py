from tastypie.api import Api

from .resources.billing import CreateBillingConfigurationResource
from .resources.package import BangoProductResource, PackageResource
from .resources.premium import MakePremiumResource
from .resources.rating import UpdateRatingResource


bango = Api(api_name='bango')
for lib in (PackageResource, BangoProductResource, MakePremiumResource,
            UpdateRatingResource, CreateBillingConfigurationResource):
    bango.register(lib())
