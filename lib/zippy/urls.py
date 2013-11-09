from django.conf.urls import patterns, url

from .views import ProxyView

urlpatterns = patterns('',
    url(r'^(?P<reference_name>\w+)/(?P<resource_name>\w+)/(?P<uuid>[^/]+)?/?',
        ProxyView.as_view(), name='zippy.api_view'),
)
