from django.conf.urls import include, patterns

from tastypie.api import Api

from solitude.tests.resources import FakeResource


api = Api(api_name='test')
api.register(FakeResource())

urlpatterns = patterns(
    '',
    (r'^', include(api.urls)),
)
