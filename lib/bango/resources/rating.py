from cached import Resource

from lib.bango.client import get_client
from lib.bango.forms import UpdateRatingForm


class UpdateRatingResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'update-rating'
        list_allowed_methods = ['post']

    def obj_create(self, bundle, request, **kwargs):
        form = UpdateRatingForm(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        get_client().UpdateRating(form.bango_data)
        # It looks like we don't get a response to do anything with.
        return bundle
