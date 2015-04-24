from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r'^token/generate/$', 'lib.brains.views.generate',
        name='token.generate'),
)
