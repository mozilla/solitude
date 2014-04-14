from django.conf.urls import url

from rest_framework.routers import DefaultRouter

from lib.boku.views import SellerBokuViewSet, BokuTransactionView

router = DefaultRouter()
router.register(r'seller', SellerBokuViewSet)

urlpatterns = router.urls
urlpatterns += [
    url(
        r'transaction',
        BokuTransactionView.as_view(),
        name='start_transaction'
    ),
]
