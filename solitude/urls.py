from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

from funfactory.monkeypatches import patch
from tastypie.api import Api

from lib.buyers.resource import BuyerResource

api = Api(api_name='1')
api.register(BuyerResource())

patch()
urlpatterns = patterns('',
    url(r'^', include(api.urls)),
    url(r'^$', 'solitude.views.home')
)


handler500 = handler404 = handler403 = 'solitude.views.error'
