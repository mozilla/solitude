from tastypie import fields

from solitude.base import Resource


class Fake(object):
    name = ''
    pk = 0


class FakeResource(Resource):
    name = fields.CharField(attribute='name')

    class Meta(Resource.Meta):
        resource_name = 'fake'
        list_allowed_methods = ['post']
        object_class = Fake

    def obj_create(self, bundle, request, **kwargs):
        bundle.obj = Fake()
        return bundle

    def get_resource_uri(self, bundle):
        return '/'


