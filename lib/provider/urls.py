from django.conf.urls import include, patterns, url

from rest_framework.routers import DefaultRouter

from .bango import ProductView
from .boku import Event
from .reference import SellerProductReferenceView, SellerReferenceView
from .views import NotImplementedView, ProxyView

bango_overrides = patterns('',
    url(r'^product/$', ProductView.as_view(), name='provider.bango.product'),
    url(r'', NotImplementedView.as_view(), name='provider.bango.nope')
)

boku = DefaultRouter()
boku.register('event', Event, base_name='event')

reference = DefaultRouter()
reference.register('seller', SellerReferenceView)
reference.register('sellerproduct', SellerProductReferenceView)

urlpatterns = patterns('',
    url(r'^bango/', include(bango_overrides)),
    url(r'^boku/', include(boku.urls)),
    # TODO: once I feel comfortable this is good, we'll remove beta so
    # it overrides existing URLs. This allows lots of smaller pull requests.
    url(r'^reference-beta/', include(reference.urls, namespace='ref')),
    url(r'^(?P<reference_name>\w+)/(?P<resource_name>\w+)/(?P<uuid>[^/]+)?/?',
        ProxyView.as_view(), name='provider.api_view'),
)
