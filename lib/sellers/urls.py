from rest_framework.routers import DefaultRouter

from lib.sellers import views

router = DefaultRouter()
router.register(r'seller', views.SellerViewSet)
router.register(r'product', views.SellerProductViewSet)

urlpatterns = router.urls
