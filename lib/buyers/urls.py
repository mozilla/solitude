from django.conf.urls import include, patterns, url

from rest_framework.routers import DefaultRouter

from lib.buyers import views

router = DefaultRouter()
router.register(r'buyer', views.BuyerViewSet)

urlpatterns = patterns(
    '',
    url(r'', include(router.urls)),
    url(r'^generic/buyer/(?P<pk>[\d]+)/close/$', views.close, name='close'),
    url(r'^confirm_pin', views.confirm_pin, name='confirm'),
    url(r'^verify_pin', views.verify_pin, name='verify'),
    url(r'^reset_confirm_pin', views.reset_confirm_pin,
        name='reset_confirm_pin')
)
