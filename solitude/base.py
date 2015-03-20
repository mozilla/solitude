import functools
import json
import sys
import traceback
import uuid
import warnings
from hashlib import md5

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.urlresolvers import resolve, reverse
from django.db import models, transaction
from django.db.models import F
from django.db.models.query import QuerySet
from django.db.models.sql.constants import LOOKUP_SEP, QUERY_TERMS
from django.http import HttpResponse, Http404
from django.test.client import Client
from django.utils.decorators import method_decorator
from django.views import debug
from django.views.decorators.http import etag

from cef import log_cef as _log_cef

from rest_framework import serializers, status
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from tastypie import http
from tastypie.authorization import Authorization
from tastypie.exceptions import ImmediateHttpResponse, InvalidFilterError
from tastypie.fields import ToOneField
from tastypie.resources import (ModelResource as TastyPieModelResource,
                                Resource as TastyPieResource,
                                convert_post_to_patch)
from tastypie.utils import dict_strip_unicode_keys
from tastypie.validation import FormValidation
from django import test

from solitude.authentication import OAuthAuthentication
from solitude.logger import getLogger
from solitude.related_fields import PathRelatedField


log = getLogger('s')
dump_log = getLogger('s.dump')
sys_cef_log = getLogger('s.cef')
tasty_log = getLogger('django.request.tastypie')


def etag_func(request, data, *args, **kwargs):
    if hasattr(request, 'initial_etag'):
        all_etags = [str(request.initial_etag)]
    else:
        if data:
            try:
                objects = [data.obj]  # Detail case.
            except AttributeError:
                try:
                    objects = data['objects']  # List case.
                except (TypeError, KeyError):
                    if isinstance(data, QuerySet):  # DRF case.
                        objects = data
                    else:
                        return None
        if objects:
            try:
                all_etags = [str(obj['etag']) for obj in objects]
            except (TypeError, KeyError):
                try:
                    all_etags = [str(obj.etag) for obj in objects]
                except AttributeError:
                    try:
                        all_etags = [str(bundle.obj.etag)
                                     for bundle in objects]
                    except AttributeError:
                        return None
        else:
            return None
    return md5(''.join(all_etags)).hexdigest()


old = debug.technical_500_response


def json_response(request, exc_type, exc_value, tb):
    # If you are doing requests in debug mode from say, curl,
    # it's nice to be able to get some JSON back for an error, not a
    # gazillion lines of HTML.
    if request.META['CONTENT_TYPE'] == 'application/json':
        return http.HttpApplicationError(
            content=json.dumps({'traceback':
                                traceback.format_tb(tb),
                                'type': str(exc_type),
                                'value': str(exc_value)}),
            content_type='application/json; charset=utf-8')

    return old(request, exc_type, exc_value, tb)

debug.technical_500_response = json_response


def json_parse(fn):
    """Wrapper around responses to add additional info."""
    @functools.wraps(fn)
    def wrapper(*args, **kw):
        response = fn(*args, **kw)

        def _json(self):
            """Will return parsed JSON on response if there is any."""
            if self.content and 'application/json' in self['Content-Type']:
                if not hasattr(self, '_content_json'):
                    self._content_json = json.loads(self.content)
                return self._content_json

        response.json = property(_json)
        return response
    return wrapper


class APIClient(Client):

    def _process(self, kwargs):
        if 'content_type' not in kwargs:
            kwargs['content_type'] = 'application/json'
        if 'data' in kwargs and kwargs['content_type'] == 'application/json':
            kwargs['data'] = json.dumps(kwargs['data'])
        return kwargs

    @json_parse
    def get(self, *args, **kwargs):
        return super(APIClient, self).get(*args, **kwargs)

    @json_parse
    def get_with_body(self, *args, **kwargs):
        # The Django test client automatically serializes data, not allowing
        # you to do a GET with a body. We want to be able to do that in our
        # tests.
        return super(APIClient, self).post(*args, REQUEST_METHOD='GET',
                                           **self._process(kwargs))

    @json_parse
    def post(self, *args, **kwargs):
        return super(APIClient, self).post(*args, **self._process(kwargs))

    @json_parse
    def put(self, *args, **kwargs):
        return super(APIClient, self).put(*args, **self._process(kwargs))

    @json_parse
    def patch(self, *args, **kwargs):
        return super(APIClient, self).put(*args, REQUEST_METHOD='PATCH',
                                          **self._process(kwargs))


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

    def get_list_url(self, name, api_name=None):
        return reverse('api_dispatch_list',
                       kwargs={'api_name': api_name or self.api_name,
                               'resource_name': name})

    def get_detail_url(self, name, pk, api_name=None):
        pk = getattr(pk, 'pk', pk)
        return reverse('api_dispatch_detail',
                       kwargs={'api_name': api_name or self.api_name,
                               'resource_name': name, 'pk': pk})

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


class Authorization(Authorization):
    pass


def get_object_or_404(cls, **filters):
    """
    A wrapper around our more familiar get_object_or_404, for when we need
    to get access to an object that isn't covered by get_obj.
    """
    if not filters:
        raise ImmediateHttpResponse(response=http.HttpNotFound())
    try:
        return cls.objects.get(**filters)
    except (cls.DoesNotExist, cls.MultipleObjectsReturned):
        raise ImmediateHttpResponse(response=http.HttpNotFound())


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


def handle_500(request, exception):
    # Print some nice 500 errors back to the clients if not in debug mode.
    tb = traceback.format_tb(sys.exc_traceback)
    tasty_log.error(
        '%s: %s %s\n%s' % (
            request.path,
            exception.__class__.__name__, exception,
            '\n'.join(tb)
        ),
        extra={'status_code': 500, 'request': request},
        exc_info=sys.exc_info()
    )
    data = {
        'error_message': str(exception),
        'error_code': getattr(exception, 'id',
                              exception.__class__.__name__),
        'error_data': getattr(exception, 'data', {})
    }
    # We'll also cef log any errors.
    log_cef(str(exception), request, severity=3)
    return http.HttpApplicationError(
        content=json.dumps(data),
        content_type='application/json; charset=utf-8'
    )


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
    Retains compatability between DRF and Tastypie.
    """
    resource_pk = serializers.CharField(source='pk')
    resource_uri = serializers.SerializerMethodField('get_resource_uri')

    def get_resource_uri(self, obj):
        return self.resource_uri(obj.pk)


class DRFBaseResource(object):
    """
    A TastypieBaseResource for DRF.
    """

    def form_errors(self, forms):
        return Response(format_form_errors(forms), status=400)


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


class TastypieBaseResource(object):
    """
    A TastypieBaseResource for Tastypie.
    """

    def form_errors(self, forms):
        errors = format_form_errors(forms)
        response = http.HttpBadRequest(json.dumps(errors),
                                       content_type='application/json')
        raise ImmediateHttpResponse(response=response)

    def dehydrate(self, bundle):
        bundle.data['resource_pk'] = bundle.obj.pk
        return super(TastypieBaseResource, self).dehydrate(bundle)

    def _handle_500(self, request, exception):
        return handle_500(request, exception)

    def dispatch(self, request_type, request, **kw):
        dump_request(request)
        msg = '%s:%s' % (kw.get('api_name', 'unknown'),
                         kw.get('resource_name', 'unknown'))
        log_cef(msg, request, severity=2)
        return super(TastypieBaseResource, self).dispatch(request_type,
                                                          request, **kw)

    def build_filters(self, filters=None):
        # Override the filters so we can stop Tastypie silently ignoring
        # invalid filters. That will cause an invalid filtering just to return
        # lots of results.
        if filters is None:
            filters = {}
        qs_filters = {}

        for filter_expr, value in filters.items():
            filter_bits = filter_expr.split(LOOKUP_SEP)
            field_name = filter_bits.pop(0)
            filter_type = 'exact'

            if field_name not in self.fields:
                # Don't just ignore this. Tell the world. Shame I have to
                # override all this, just to do this.
                raise InvalidFilterError('Not a valid filtering field: %s'
                                         % field_name)

            if len(filter_bits) and filter_bits[-1] in QUERY_TERMS:
                filter_type = filter_bits.pop()

            lookup_bits = self.check_filtering(field_name, filter_type,
                                               filter_bits)

            if value in ['true', 'True', True]:
                value = True
            elif value in ['false', 'False', False]:
                value = False
            elif value in ('nil', 'none', 'None', None):
                value = None

            # Split on ',' if not empty string and either an in or range
            # filter.
            if filter_type in ('in', 'range') and len(value):
                if hasattr(filters, 'getlist'):
                    value = filters.getlist(filter_expr)
                else:
                    value = value.split(',')

            db_field_name = LOOKUP_SEP.join(lookup_bits)
            qs_filter = '%s%s%s' % (db_field_name, LOOKUP_SEP, filter_type)
            qs_filters[qs_filter] = value

        return dict_strip_unicode_keys(qs_filters)

    def is_valid(self, bundle, request):
        # Tastypie will check is_valid on the object by validating the form,
        # but on PUTes and PATCHes it does so without instantiating the object.
        # Without the object on the model.instance, the uuid check does not
        # exclude the original object being changed and so the validation
        # will fail. This patch will force the object to be added before
        # validation,
        #
        # There are two ways to spot when we should be doing this:
        # 1. When there is a specific resource_pk in the PUT or PATCH.
        # 2. When the request.path resolves to having a pk in it.
        # If either of those match, get_via_uri will do the right thing.
        if 'resource_uri' in bundle.data or 'pk' in resolve(request.path)[2]:
            try:
                bundle.obj = self.get_via_uri(request.path)
                if request.method == 'PUT':
                    # In case of a PUT modification, we need to keep
                    # the initial values for the given object to check
                    # the Etag header.
                    request.initial_etag = getattr(bundle.obj, 'etag', '')
            except ObjectDoesNotExist:
                pass
        return super(TastypieBaseResource, self).is_valid(bundle, request)

    @method_decorator(etag(etag_func))
    def create_response(self, request, data, response_class=HttpResponse,
                        **response_kwargs):
        return super(TastypieBaseResource, self).create_response(
            request, data, response_class, **response_kwargs)

    @method_decorator(etag(etag_func))
    def create_patch_response(self, request, original_bundle, new_data):
        self.update_in_place(request, original_bundle, new_data)
        return http.HttpAccepted()

    def patch_detail(self, request, **kwargs):
        request = convert_post_to_patch(request)
        try:
            obj = self.cached_obj_get(
                request=request, **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return http.HttpNotFound()
        except MultipleObjectsReturned:
            return http.HttpMultipleChoices('More than one resource'
                                            'is found at this URI.')

        bundle = self.build_bundle(obj=obj, request=request)
        bundle = self.full_dehydrate(bundle)
        bundle = self.alter_detail_data_to_serialize(request, bundle)

        # Now update the bundle in-place.
        deserialized = self.deserialize(
            request, request.body,
            format=request.META.get('CONTENT_TYPE', 'application/json'))

        # In case of a patch modification, we need to store
        # the initial values for the given object to check
        # the Etag header.
        request.initial_etag = bundle.obj.etag
        return self.create_patch_response(request, bundle, deserialized)

    def deserialize_body(self, request):
        # Trying to standardize on JSON in the body for most things if we
        # can. Similar to elastic search. Retaining query string for tastypie
        # record filtering.
        data = request.body
        if not data:
            # Don't raise an error if the body is empty.
            return {}

        return self.deserialize(request, data, format='application/json')


class ModelFormValidation(FormValidation):

    def is_valid(self, bundle, request=None):
        # Based on is_valid above, we are getting the object into
        # bundle.obj. Now lets pass that into the instance, so that normal
        # form validation works.
        data = bundle.data
        if data is None:
            data = {}

        form = self.form_class(data, instance=bundle.obj)
        if form.is_valid():
            return {}
        return form.errors


class Resource(TastypieBaseResource, TastyPieResource):

    class Meta:
        always_return_data = True
        authentication = OAuthAuthentication()
        authorization = Authorization()


class ModelResource(TastypieBaseResource, TastyPieModelResource):

    class Meta:
        always_return_data = True
        authentication = OAuthAuthentication()
        authorization = Authorization()


class Cached(object):

    def __init__(self, prefix='cached', pk=None):
        pk = pk if pk else uuid.uuid4()
        self.prefixed = '%s:%s' % (prefix, pk)
        self.pk = pk

    def set(self, data):
        return cache.set(self.prefixed, data)

    def get(self):
        return cache.get(self.prefixed)

    def get_or_404(self):
        res = self.get()
        if not res:
            raise ImmediateHttpResponse(response=http.HttpNotFound())
        return res

    def delete(self):
        cache.delete(self.prefixed)


class ManagerBase(models.Manager):

    def safer_get_or_create(self, defaults=None, **kw):
        """
        This is subjective, but I don't trust get_or_create until #13906
        gets fixed. It's probably fine, but this makes me happy for the moment
        and solved a get_or_create we've had in the past.
        """
        with transaction.commit_on_success():
            try:
                return self.get(**kw), False
            except self.model.DoesNotExist:
                if defaults is not None:
                    kw.update(defaults)
                return self.create(**kw), True


class Model(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    counter = models.BigIntegerField(null=True, blank=True, default=0)
    objects = ManagerBase()

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
        return md5('%s:%s' % (self.pk, self.counter)).hexdigest()


def invert(data):
    """
    Helper to turn a dict of constants into a choices tuple.
    """
    return [(v, k) for k, v in data.items()]


class CompatRelatedField(PathRelatedField):
    """
    Compatible field for connecting Tastypie resources to
    django-rest-framework instances.
    """

    def __init__(self, *args, **kwargs):
        self.tastypie = kwargs.pop('tastypie')
        return super(CompatRelatedField, self).__init__(*args, **kwargs)

    def to_native(self, obj):
        # If the object has not yet been saved then we cannot hyperlink to it.
        if getattr(obj, 'pk', None) is None:
            return

        self.tastypie['pk'] = obj.pk
        return reverse('api_dispatch_detail', kwargs=self.tastypie)


class CompatToOneField(ToOneField):

    def __init__(self, *args, **kwargs):
        self.rest = kwargs.pop('rest')
        return super(CompatToOneField, self).__init__(*args, **kwargs)

    def dehydrate_related(self, bundle, related_resource):
        return reverse(self.rest + '-detail', kwargs={'pk': bundle.obj.pk})


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
    def retrieve_response(self, request, data):
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(self.object)
        return self.retrieve_response(request, serializer.data)


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
    pass
