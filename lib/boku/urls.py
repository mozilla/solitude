from rest_framework.routers import DefaultRouter

from .views import SellerBokuViewSet

router = DefaultRouter()
router.register(r'seller', SellerBokuViewSet)

urlpatterns = router.urls
