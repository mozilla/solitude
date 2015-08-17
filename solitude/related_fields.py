import urlparse

from django.forms.fields import Field

from rest_framework.relations import HyperlinkedRelatedField


class RelativePathMixin(object):

    def get_url(self, *args, **kwargs):
        url = super(RelativePathMixin, self).get_url(*args, **kwargs)
        parsed = urlparse.urlparse(url)
        return parsed.path


class PathRelatedField(RelativePathMixin, HyperlinkedRelatedField):
    pass


class PathRelatedFormField(RelativePathMixin, HyperlinkedRelatedField, Field):

    """
    A variant of the PathRelatedField that can be used in Django Forms.
    """

    def __init__(self, *args, **kwargs):
        # This is in DRF 3.0, remove this in bug #416.
        self.allow_null = kwargs.pop('allow_null', False)

        queryset = kwargs.pop('queryset')
        super(PathRelatedFormField, self).__init__(*args, **kwargs)
        # __init__ sets queryset to be None, ensure we set it afterwards.
        self.queryset = queryset

    def to_python(self, value):
        if not value and self.allow_null:
            return None
        # Map the form method to the serializer version.
        return self.from_native(value)
