from django.conf.urls import include, patterns, url

from rest_framework.routers import SimpleRouter
from tastypie.api import Api

from .resources import simple
from .resources.billing import CreateBillingConfigurationResource
from .resources.login import login
from .resources.notification import EventResource, NotificationResource
from .resources.package import BangoProductResource, PackageResource
from .resources.refund import RefundResource
from .resources.sbi import SBIResource
from .resources.status import DebugViewSet, StatusViewSet

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


# TODO: would be nice to have these a sub objects of the
# bango package instead of being on their own.
bango_drf = SimpleRouter()
bango_drf.register('status', StatusViewSet)
bango_drf.register('debug', DebugViewSet, base_name='debug')

urlpatterns = patterns(
    '',
    url(r'^login/', login, name='bango.login'),
    url(r'^', include(bango_drf.urls)),
)
