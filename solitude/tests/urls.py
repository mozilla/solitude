from django.conf.urls.defaults import include, patterns
from solitude.tests.resources import FakeResource

from tastypie.api import Api


api = Api(api_name='test')
api.register(FakeResource())

urlpatterns = patterns('',
    (r'^', include(api.urls)),
)
