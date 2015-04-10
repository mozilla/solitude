from rest_framework.routers import DefaultRouter

from lib.transactions import views

router = DefaultRouter()
router.register(r'transaction', views.TransactionViewSet)

urlpatterns = router.urls
