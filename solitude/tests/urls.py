from django.conf.urls.defaults import include, patterns
from solitude.tests.resources import FakeResource, FakeServiceResource

from tastypie.api import Api


api = Api(api_name='test')
api.register(FakeResource())
api.register(FakeServiceResource())

urlpatterns = patterns('',
    (r'^', include(api.urls)),
)
