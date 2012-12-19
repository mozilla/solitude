from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.utils import importlib

from tastypie.exceptions import NotFound


class URLField(forms.CharField):
    """
    This is a tastypie like field that takes in a URL to a resource
    and then turns it into the object. Tastypie probably did this
    already and I didn't notice.
    """

    def __init__(self, to=None, *args, **kw):
        self.to = to
        super(URLField, self).__init__(*args, **kw)

    def to_instance(self):
        module_bits = self.to.split('.')
        module_path, class_name = '.'.join(module_bits[:-1]), module_bits[-1]
        module = importlib.import_module(module_path)
        try:
            return getattr(module, class_name, None)()
        except TypeError:
            raise ValueError('%s is not valid' % self.to)

    def clean(self, value):
        super(URLField, self).clean(value)
        if not value:
            return

        try:
            return self.to_instance().get_via_uri(value)
        except (ObjectDoesNotExist, NotFound):
            raise forms.ValidationError('Not a valid resource.')


class ListField(forms.CharField):

    def clean(self, value):
        if not isinstance(value, list):
            raise forms.ValidationError('Invalid list.')
        return value
