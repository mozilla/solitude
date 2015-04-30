from django.conf.urls import include, patterns, url

from rest_framework.routers import DefaultRouter

from lib.brains.views import buyer

router = DefaultRouter()
router.register(r'buyer', buyer.BraintreeBuyerViewSet, base_name='buyer')

urlpatterns = patterns(
    'lib.brains.views',
    url(r'', include(router.urls)),
    url(r'^token/generate/$', 'token.generate', name='token.generate'),
    url(r'^customer/$', 'customer.create', name='customer'),

)
