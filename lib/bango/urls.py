from tastypie.api import Api

from .resources import PackageResource

bango = Api(api_name='bango')
bango.register(PackageResource())
