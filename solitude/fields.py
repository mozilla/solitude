from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import get_script_prefix, resolve, Resolver404
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

    def get_via_uri(self, uri, request=None):
        """
        Like get_via_uri from tastypie, but ignores resource_name
        and reference_name, get_via_uri assumes everything in the URI
        should be passed to get_obj.
        """
        prefix = get_script_prefix()
        chomped_uri = uri

        if prefix and chomped_uri.startswith(prefix):
            chomped_uri = chomped_uri[len(prefix)-1:]

        try:
            view, args, kwargs = resolve(chomped_uri)
        except Resolver404:
            raise NotFound("The URL provided '%s' was not "
                           "a link to a valid resource." % uri)

        return dict((k, v) for k, v in kwargs.items()
                    if k not in ['api_name', 'resource_name',
                                 'reference_name'])

    def clean(self, value):
        super(URLField, self).clean(value)
        if not value:
            return

        try:
            kwargs = self.get_via_uri(value)
            return self.to_instance().obj_get(**kwargs)
        except (ObjectDoesNotExist, NotFound):
            raise forms.ValidationError('Not a valid resource.')


class ListField(forms.CharField):

    def clean(self, value):
        if not isinstance(value, list):
            raise forms.ValidationError('Invalid list.')
        return value
