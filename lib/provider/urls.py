from django.conf.urls import include, patterns, url

from rest_framework.routers import DefaultRouter

from .bango import ProductView
from .boku import Event
from .reference import SellerProductReference, SellerReference, Terms
from .views import NotImplementedView, ProxyView

bango_overrides = patterns(
    '',
    url(r'^product/$', ProductView.as_view(), name='provider.bango.product'),
    url(r'', NotImplementedView.as_view(), name='provider.bango.nope')
)

boku = DefaultRouter()
boku.register('event', Event, base_name='event')

reference = DefaultRouter()
reference.register('sellers', SellerReference, base_name='sellers')
reference.register('products', SellerProductReference, base_name='products')
reference.register('terms', Terms, base_name='terms')

urlpatterns = patterns(
    '',
    url(r'^bango/', include(bango_overrides)),
    url(r'^boku/', include(boku.urls)),
    url(r'^reference/', include(reference.urls, namespace='reference')),

    # The catch all for everything else that has not be viewsetted.
    url(r'^(?P<reference_name>\w+)/(?P<resource_name>\w+)/(?P<uuid>[^/]+)?/?',
        ProxyView.as_view(), name='provider.api_view'),
)
