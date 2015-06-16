import functools
import json
import warnings
from hashlib import md5

from django import test
from django.conf import settings
from django.db import models
from django.db.models import F
from django.db.models.query import QuerySet
from django.forms import model_to_dict
from django.http import Http404
from django.test.client import Client
from django.utils.decorators import method_decorator
from django.views.decorators.http import etag

from cef import log_cef as _log_cef
from rest_framework import mixins
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.utils.encoders import JSONEncoder

from solitude.logger import getLogger

log = getLogger('s')
dump_log = getLogger('s.dump')
sys_cef_log = getLogger('s.cef')


def get_objects(data):
    # If its a Serializer.
    if isinstance(data, BaseSerializer):
        return [data.object]

    # If its a queryset.
    if isinstance(data, QuerySet):
        return data


def etag_func(request, data, *args, **kwargs):
    all_etags = []
    if hasattr(request, 'initial_etag'):
        all_etags = [str(request.initial_etag)]
    else:
        objects = get_objects(data)
        if data and objects:
            all_etags = [str(obj.etag) for obj in objects]

    return md5(''.join(all_etags)).hexdigest()


class _JSONifiedResponse(object):

    def __init__(self, response):
        self._orig_response = response

    def __getattr__(self, n):
        return getattr(self._orig_response, n)

    def __getitem__(self, n):
        return self._orig_response[n]

    def __iter__(self):
        return iter(self._orig_response)

    @property
    def json(self):
        """Will return parsed JSON on response if there is any."""
        if self.content and 'application/json' in self['Content-Type']:
            if not hasattr(self, '_content_json'):
                self._content_json = json.loads(self.content)
            return self._content_json


class APIClient(Client):

    def _process(self, kwargs):
        if 'content_type' not in kwargs:
            kwargs['content_type'] = 'application/json'
        if 'data' in kwargs and kwargs['content_type'] == 'application/json':
            kwargs['data'] = json.dumps(kwargs['data'])
        return kwargs

    def _with_json(self, response):
        if hasattr(response, 'json'):
            return response
        else:
            return _JSONifiedResponse(response)

    def get(self, *args, **kwargs):
        return self._with_json(super(APIClient, self)
                               .get(*args, **self._process(kwargs)))

    def get_with_body(self, *args, **kwargs):
        # The Django test client automatically serializes data, not allowing
        # you to do a GET with a body. We want to be able to do that in our
        # tests.
        return self._with_json(super(APIClient, self)
                               .post(*args, REQUEST_METHOD='GET',
                                     **self._process(kwargs)))

    def post(self, *args, **kwargs):
        return self._with_json(super(APIClient, self)
                               .post(*args, **self._process(kwargs)))

    def put(self, *args, **kwargs):
        return self._with_json(super(APIClient, self)
                               .put(*args, CONTENT_TYPE='application/json',
                                    **self._process(kwargs)))

    def patch(self, *args, **kwargs):
        return self._with_json(super(APIClient, self)
                               .put(*args, REQUEST_METHOD='PATCH',
                                    **self._process(kwargs)))


class APITest(test.TestCase):
    client_class = APIClient

    def _pre_setup(self):
        super(APITest, self)._pre_setup()
        # For unknown reasons test_utils sets settings.DEBUG = True.
        # For more unknown reasons tastypie won't show you any error
        # tracebacks if settings.DEBUG = False.
        #
        # Let's set this to True so we've got a hope in hell of
        # debugging errors in the tests.
        settings.DEBUG = True

    def allowed_verbs(self, url, allowed):
        """
        Will run through all the verbs except the ones specified in allowed
        and ensure that hitting those produces a 401 or a 405.
        Otherwise the test will fail.
        """
        verbs = ['get', 'post', 'put', 'delete', 'patch']
        for verb in verbs:
            if verb in allowed:
                continue
            res = getattr(self.client, verb)(url)
            assert res.status_code in (401, 405), (
                '%s: %s not 401 or 405' % (verb.upper(), res.status_code))

    def get_errors(self, content, field):
        return json.loads(content)[field]

    def mozilla_error(self, content, field):
        return [f['code'] for f in content['mozilla'][field]]

    def braintree_error(self, content, field):
        return [f['code'] for f in content['braintree'][field]]

    def print_as_json(self, data):
        """
        A utility function used to dump the json to stdout. Useful in tests
        when you want some output for documentation.
        """
        print json.dumps(data, indent=2, cls=JSONEncoder)


def log_cef(msg, request, **kw):
    g = functools.partial(getattr, settings)
    severity = kw.pop('severity', g('CEF_DEFAULT_SEVERITY', 5))
    cef_kw = {
        'msg': msg,
        'signature': request.get_full_path(),
        'config': {
            'cef.product': 'Solitude',
            'cef.vendor': g('CEF_VENDOR', 'Mozilla'),
            'cef.version': g('CEF_VERSION', '0'),
            'cef.device_version': g('CEF_DEVICE_VERSION', '0'),
            'cef.file': g('CEF_FILE', 'syslog'),
        }
    }

    if severity > 2:
        # Only send more severe logging to syslog. Messages lower than that
        # could be every http request, etc.
        sys_cef_log.error('CEF Severity: {sev} Message: {msg}'
                          .format(sev=severity, msg=msg))

    # Allow the passing of additional cs* values.
    for k, v in kw.items():
        if k.startswith('cs'):
            cef_kw[k] = v

    _log_cef(msg, severity, request.META.copy(), **cef_kw)


def format_form_errors(forms):
    errors = {}
    if not isinstance(forms, list):
        forms = [forms]
    for f in forms:
        log.info('Error processing form: {0}'.format(f.__class__.__name__))
        if isinstance(f.errors, list):  # Cope with formsets.
            for e in f.errors:
                errors.update(e)
            continue
        errors.update(dict(f.errors.items()))

    return errors


def dump_request(request=None, **kw):
    """
    Dumps the request out to a log.

    :param request: a request object, optional
    :param kw: if request is None, looks up the value in kw
    """
    if not settings.DUMP_REQUESTS:
        return

    method = request.method if request else kw.get('method', '')
    url = request.get_full_path() if request else kw.get('url')
    body = request.body if request else kw.get('body')

    dump_log.debug('request method: {0}'.format(method.upper()))
    dump_log.debug('request url: {0}'.format(url))
    dump_log.debug('request body: {0}'.format(body))
    for hdr, value in kw.get('headers', {}).items():
        dump_log.debug('request header: {0}: {1}'.format(hdr, value))


def dump_response(response=None, **kw):
    """
    Dumps the response out to a log.

    :param response: a response object, optional
    :param kw: if response is None, looks up the value in kw
    """
    if not settings.DUMP_REQUESTS:
        return

    state = response.status_code if response else kw.get('status_code')
    body = response.text if response else kw.get('text', '')
    headers = response.headers if response else kw.get('headers')

    dump_log.debug('response status: {0}'.format(state))
    dump_log.debug('response body: {0}'.format(body))
    for hdr, value in headers.items():
        dump_log.debug('response header: {0}: {1}'.format(hdr, value))


class BaseSerializer(serializers.ModelSerializer):

    """
    Standard base serializer for solitude objects.
    """
    resource_pk = serializers.CharField(source='pk', read_only=True)
    resource_uri = serializers.SerializerMethodField('get_resource_uri')

    def get_resource_uri(self, obj):
        return self.resource_uri(obj.pk)


class BaseAPIView(APIView):

    """
    A base APIView for DRF that we can subclass everything off of.
    """

    def dispatch(self, request, *args, **kwargs):
        dump_request(request)
        msg = '%s:%s' % (kwargs.get('reference_name', 'unknown'),
                         kwargs.get('resource_name', 'unknown'))
        log_cef(msg, request, severity=2)
        return super(BaseAPIView, self).dispatch(request, *args, **kwargs)

    def form_errors(self, forms):
        return Response(format_form_errors(forms), status=400)


class Model(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    counter = models.BigIntegerField(null=True, blank=True, default=0)

    class Meta:
        abstract = True
        ordering = ('-created',)
        get_latest_by = 'created'

    def reget(self):
        return self.__class__.objects.get(pk=self.pk)

    def save(self, *args, **kw):
        if self.pk:
            self.counter = F('counter') + 1
        super(Model, self).save(*args, **kw)

    @property
    def etag(self):
        return '%s:%s' % (self.pk, self.counter)

    def to_dict(self):
        data = model_to_dict(self)
        data.update({
            'created': self.created,
            'modified': self.modified,
            'counter': self.counter
        })
        return data


def invert(data):
    """
    Helper to turn a dict of constants into a choices tuple.
    """
    return [(v, k) for k, v in data.items()]


class UpdateModelMixin(mixins.UpdateModelMixin):

    """
    Turns the django-rest-framework mixin into an etag-aware one.
    """
    @method_decorator(etag(etag_func))
    def update_response(self, request, data, serializer, save_kwargs,
                        created, success_status_code):
        self.pre_save(serializer.object)
        self.object = serializer.save(**save_kwargs)
        self.post_save(self.object, created=created)
        return Response(serializer.data, status=success_status_code)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        self.object = self.get_object_or_none()

        if self.object is None:
            created = True
            save_kwargs = {'force_insert': True}
            success_status_code = status.HTTP_201_CREATED
        else:
            created = False
            save_kwargs = {'force_update': True}
            success_status_code = status.HTTP_200_OK

        serializer = self.get_serializer(self.object, data=request.DATA,
                                         files=request.FILES, partial=partial)

        if serializer.is_valid():
            request.initial_etag = serializer.object.etag
            return self.update_response(request, serializer.object,
                                        serializer, save_kwargs,
                                        created, success_status_code)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListModelMixin(object):

    """
    Turns the django-rest-framework mixin into an etag-aware one.
    """
    empty_error = "Empty list and '%(class_name)s.allow_empty' is False."

    @method_decorator(etag(etag_func))
    def list_response(self, request, data):
        # Switch between paginated or standard style responses
        page = self.paginate_queryset(self.object_list)
        if page is not None:
            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(self.object_list, many=True)

        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        self.object_list = self.filter_queryset(self.get_queryset())

        # Default is to allow empty querysets.  This can be altered by setting
        # `.allow_empty = False`, to raise 404 errors on empty querysets.
        if not self.allow_empty and not self.object_list:
            warnings.warn(
                'The `allow_empty` parameter is due to be deprecated. '
                'To use `allow_empty=False` style behavior, You should '
                'override `get_queryset()` and explicitly raise a 404 on '
                'empty querysets.',
                PendingDeprecationWarning
            )
            class_name = self.__class__.__name__
            error_msg = self.empty_error % {'class_name': class_name}
            raise Http404(error_msg)

        return self.list_response(request, self.object_list)


class RetrieveModelMixin(object):

    """
    Turns the django-rest-framework mixin into an etag-aware one.
    """
    @method_decorator(etag(etag_func))
    def retrieve_response(self, request, serializer):
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(self.object)
        return self.retrieve_response(request, serializer)


class NonDeleteModelViewSet(
        mixins.CreateModelMixin,
        RetrieveModelMixin,
        mixins.RetrieveModelMixin,
        UpdateModelMixin,
        ListModelMixin,
        GenericViewSet):

    """
    Same as the ModelViewSet, without the DeleteMixin. Uses our local mixins
    to give us ETag support.
    """

    def form_errors(self, forms):
        return Response(format_form_errors(forms), status=400)
