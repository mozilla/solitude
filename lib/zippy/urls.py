from django.conf.urls import patterns, url

from .views import api_view

urlpatterns = patterns('',
    url(r'^(?P<reference_name>\w+)/(?P<resource_name>\w+)/',
        api_view, name='zippy.api_view'),
)
