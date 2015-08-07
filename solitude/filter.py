from rest_framework.filters import DjangoFilterBackend

from solitude.errors import InvalidQueryParams
from solitude.logger import getLogger

log = getLogger('s.filter')


class StrictQueryFilter(DjangoFilterBackend):

    """
    Don't allow people to typo request params and return all the objects.
    Instead limit it down to the parameters allowed in filter_fields.
    """

    def get_filter_class(self, view, queryset=None):
        klass = (super(StrictQueryFilter, self)
                 .get_filter_class(view, queryset=queryset))
        try:
            # If an ordering exists on the model, use that.
            klass._meta.order_by = klass.Meta.model.Meta.ordering
        except AttributeError:
            pass
        return klass

    def filter_queryset(self, request, queryset, view):
        requested = set(request.QUERY_PARAMS.keys())
        allowed = set(getattr(view, 'filter_fields', []))
        difference = requested.difference(allowed)
        if difference:
            raise InvalidQueryParams(
                detail='Incorrect query parameters: ' + ','.join(difference))

        return (super(StrictQueryFilter, self)
                .filter_queryset(request, queryset, view))
