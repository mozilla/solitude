from django.conf.urls import include, patterns, url

from rest_framework.routers import DefaultRouter

from lib.brains.views import buyer, paymethod, subscription, transaction

router = DefaultRouter()
router.register(r'buyer', buyer.BraintreeBuyerViewSet, base_name='buyer')
router.register(r'paymethod', paymethod.PaymentMethodViewSet,
                base_name='paymethod')
router.register(r'subscription', subscription.SubscriptionViewSet,
                base_name='subscription')
router.register(r'transaction', transaction.TransactionViewSet,
                base_name='transaction')

urlpatterns = patterns(
    'lib.brains.views',
    url(r'^mozilla/', include(router.urls, namespace='mozilla')),
    url(r'^token/generate/$', 'token.generate', name='token.generate'),
    url(r'^customer/$', 'customer.create', name='customer'),
    url(r'^paymethod/$', 'paymethod.create', name='paymethod'),
    url(r'^paymethod/delete/$', 'paymethod.delete', name='paymethod.delete'),
    url(r'^subscription/$', 'subscription.create', name='subscription'),
    url(r'^subscription/cancel/$', 'subscription.cancel',
        name='subscription.cancel'),
    url(r'^subscription/paymethod/change/$', 'subscription.change',
        name='subscription.change'),
    url(r'^webhook/$', 'webhook.webhook', name='webhook'),
)
