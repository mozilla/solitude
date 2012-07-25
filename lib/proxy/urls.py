from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^', 'lib.proxy.views.proxy')
)
