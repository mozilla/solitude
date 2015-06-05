from rest_framework.filters import DjangoFilterBackend

from solitude.errors import InvalidQueryParams


class StrictQueryFilter(DjangoFilterBackend):

    """
    Don't allow people to typo request params and return all the objects.
    Instead limit it down to the parameters allowed in filter_fields.
    """

    def filter_queryset(self, request, queryset, view):
        requested = set(request.QUERY_PARAMS.keys())
        allowed = set(getattr(view, 'filter_fields', []))
        difference = requested.difference(allowed)
        if difference:
            raise InvalidQueryParams(
                detail='Incorrect query parameters: ' + ','.join(difference))

        return (super(StrictQueryFilter, self)
                .filter_queryset(request, queryset, view))
