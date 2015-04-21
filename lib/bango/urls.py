from django.conf.urls import include, patterns, url

from rest_framework.routers import SimpleRouter

from lib.bango.views.bank import bank
from lib.bango.views.billing import billing
from lib.bango.views.event import event
from lib.bango.views.login import login
from lib.bango.views.notification import notification
from lib.bango.views.package import PackageViewSet
from lib.bango.views.premium import premium
from lib.bango.views.product import ProductViewSet
from lib.bango.views.rating import rating
from lib.bango.views.refund import RefundViewSet
from lib.bango.views.sbi import sbi
from lib.bango.views.status import DebugViewSet, StatusViewSet

bango_drf = SimpleRouter()
bango_drf.register('status', StatusViewSet, base_name='status')
bango_drf.register('debug', DebugViewSet, base_name='debug')
bango_drf.register('product', ProductViewSet, base_name='product')
bango_drf.register('package', PackageViewSet, base_name='package')
bango_drf.register('refund', RefundViewSet, base_name='refund')

urlpatterns = patterns(
    '',
    url(r'^login/$', login, name='bango.login'),
    url(r'^bank/$', bank, name='bank'),
    url(r'^premium/$', premium, name='premium'),
    url(r'^rating/$', rating, name='rating'),
    url(r'^billing/$', billing, name='billing'),
    url(r'^sbi/$', sbi, name='sbi'),
    url(r'^notification/$', notification, name='notification'),
    url(r'^event/$', event, name='event'),
    url(r'^', include(bango_drf.urls)),
)
