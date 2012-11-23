from tastypie.api import Api

from .resources.package import BangoProductResource, PackageResource
from .resources.premium import MakePremiumResource


bango = Api(api_name='bango')
bango.register(PackageResource())
bango.register(BangoProductResource())
bango.register(MakePremiumResource())
