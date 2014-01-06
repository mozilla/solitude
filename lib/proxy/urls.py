from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^paypal$', 'lib.proxy.views.paypal', name='paypal.proxy'),
    url(r'^bango$', 'lib.proxy.views.bango', name='bango.proxy'),
    url(r'^provider/(?P<reference_name>\w+)/', 'lib.proxy.views.provider',
        name='provider.proxy')
)
