from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^bango$', 'lib.proxy.views.bango', name='bango.proxy'),
    url(r'^provider/(?P<reference_name>\w+)/', 'lib.proxy.views.provider',
        name='provider.proxy'),
)
