from solitude.base import Resource


class TestError(Exception):
    pass


class ErrorResource(Resource):

    class Meta(Resource.Meta):
        list_allowed_methods = ['get']
        resource_name = 'error'

    def obj_get_list(self, request=None, **kwargs):
        # All this does is throw an error. This is used for testing
        # the error handling on dev servers.
        raise TestError
