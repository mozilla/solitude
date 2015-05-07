import os

from django.conf.urls import include, patterns, url


services_patterns = patterns(
    'lib.services.resources',
    url(r'^settings/$', 'settings_list', name='services.settings'),
    url(r'^settings/(?P<setting>[^/<>]+)/$', 'settings_view',
        name='services.setting'),
    url(r'^error/', 'error', name='services.error'),
    url(r'^logs/', 'logs', name='services.log'),
    url(r'^status/', 'status', name='services.status'),
    url(r'^request/', 'request_resource', name='services.request'),
    url(r'^failures/transactions/', 'transactions_failures',
        name='services.failures.transactions'),
    url(r'^failures/statuses/', 'statuses_failures',
        name='services.failures.statuses'),
)

generic_urls = patterns(
    '',
    url('', include('lib.buyers.urls')),
    url('', include('lib.sellers.urls')),
    url('', include('lib.transactions.urls')),
)

urls = [
    url(r'^$', 'solitude.views.home', name='home'),
    url(r'^generic/', include(generic_urls, namespace='generic')),
    url(r'^proxy/', include('lib.proxy.urls')),
    url(r'^bango/', include('lib.bango.urls', namespace='bango')),
    url(r'^braintree/', include('lib.brains.urls', namespace='braintree')),
    url(r'^provider/', include('lib.provider.urls')),
    url(r'^services/', include(services_patterns))
]

if os.getenv('IS_DOCKER'):
    urls.append(url(r'^solitude/services/', include(services_patterns)))

urlpatterns = patterns('', *urls)

handler500 = 'solitude.views.error'
handler404 = 'solitude.views.error_404'
handler403 = 'solitude.views.error_403'
