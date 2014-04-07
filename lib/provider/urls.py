from django.conf.urls import include, patterns, url

from rest_framework.routers import DefaultRouter

from .views import NotImplementedView, ProxyView
from .bango import ProductView
from .boku import Event

bango_overrides = patterns('',
    url(r'^product/$', ProductView.as_view(), name='provider.bango.product'),
    url(r'', NotImplementedView.as_view(), name='provider.bango.nope')
)

boku = DefaultRouter()
boku.register('event', Event, base_name='event')

urlpatterns = patterns('',
    url(r'^bango/', include(bango_overrides)),
    url(r'^boku/', include(boku.urls)),
    url(r'^(?P<reference_name>\w+)/(?P<resource_name>\w+)/(?P<uuid>[^/]+)?/?',
        ProxyView.as_view(), name='provider.api_view'),
)
