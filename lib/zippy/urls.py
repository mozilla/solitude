from django.conf.urls import include, patterns, url

from .views import NotImplementedView, ProxyView
from .bango import ProductView

bango_overrides = patterns('',
    url(r'^product/$', ProductView.as_view(), name='zippy.bango.product'),
    url(r'', NotImplementedView.as_view(), name='zippy.bango.nope')
)

urlpatterns = patterns('',
    url(r'^bango/', include(bango_overrides)),
    url(r'^(?P<reference_name>\w+)/(?P<resource_name>\w+)/(?P<uuid>[^/]+)?/?',
        ProxyView.as_view(), name='zippy.api_view'),
)
