from django.conf.urls import include, patterns, url

from rest_framework.routers import DefaultRouter

from .bango import ProductView
from .boku import Event
from .reference import (SellerProductReferenceView, SellerReferenceView,
                        Terms)
from .views import NotImplementedView, ProxyView

bango_overrides = patterns('',
    url(r'^product/$', ProductView.as_view(), name='provider.bango.product'),
    url(r'', NotImplementedView.as_view(), name='provider.bango.nope')
)

boku = DefaultRouter()
boku.register('event', Event, base_name='event')

urlpatterns = patterns('',
    url(r'^bango/', include(bango_overrides)),
    url(r'^boku/', include(boku.urls)),

    url(r'^reference/sellers/(?P<id>[^/]+)?/?',
        SellerReferenceView.as_view(),
        {'reference_name': 'reference', 'resource_name': 'sellers'},
        name='provider.sellers'),

    url(r'^reference/products/(?P<id>[^/]+)?/?',
        SellerProductReferenceView.as_view(),
        {'reference_name': 'reference', 'resource_name': 'products'},
        name='provider.products'),

    url(r'^reference/terms/(?P<id>[^/]+)?/?',
        Terms.as_view(),
        {'reference_name': 'reference', 'resource_name': 'terms'},
        name='provider.terms'),

    # The catch all for everything else.
    url(r'^(?P<reference_name>\w+)/(?P<resource_name>\w+)/(?P<uuid>[^/]+)?/?',
        ProxyView.as_view(), name='provider.api_view'),
)
