from django.conf.urls import include, patterns, url

from rest_framework.routers import DefaultRouter

from lib.brains.views import buyer, paymethod

router = DefaultRouter()
router.register(r'buyer', buyer.BraintreeBuyerViewSet, base_name='buyer')
router.register(r'paymethod', paymethod.PaymentMethodViewSet,
                base_name='paymethod')

urlpatterns = patterns(
    'lib.brains.views',
    url(r'^mozilla/', include(router.urls, namespace='mozilla')),
    url(r'^token/generate/$', 'token.generate', name='token.generate'),
    url(r'^customer/$', 'customer.create', name='customer'),
    url(r'^paymethod/$', 'paymethod.create', name='paymethod'),
)
