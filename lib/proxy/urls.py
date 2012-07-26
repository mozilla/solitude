from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'lib.proxy.views.proxy', name='paypal.proxy')
)
