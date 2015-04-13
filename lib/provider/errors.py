from django.http import Http404


class NoReference(Http404):

    """
    The requested reference implementation did not exist.
    """
    pass
