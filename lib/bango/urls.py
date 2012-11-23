from tastypie.api import Api

from .resources.package import BangoProductResource, PackageResource
from .resources.premium import MakePremiumResource
from .resources.rating import UpdateRatingResource


bango = Api(api_name='bango')
bango.register(PackageResource())
bango.register(BangoProductResource())
bango.register(MakePremiumResource())
bango.register(UpdateRatingResource())
