from django.conf.urls import patterns, url


urlpatterns = patterns(
    'lib.brains.views',
    url(r'^token/generate/$', 'token.generate', name='token.generate'),
    url(r'^customer/$', 'customer.create', name='customer'),
)
