import functools
import json
import logging
import sys
import traceback
import uuid

from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse, resolve
from django.db import models, transaction
from django.db.models.sql.constants import QUERY_TERMS, LOOKUP_SEP
from django.test.client import Client
from django.views import debug

curlish = False
try:
    from curlish import ANSI_CODES, get_color, print_formatted_json
    curlish = True
except ImportError:
    pass

from cef import log_cef as _log_cef
from tastypie import http
from tastypie.authorization import Authorization
from tastypie.exceptions import ImmediateHttpResponse, InvalidFilterError
from tastypie.resources import (ModelResource as TastyPieModelResource,
                                Resource as TastyPieResource)
from tastypie.utils import dict_strip_unicode_keys
from tastypie.validation import FormValidation
import test_utils

from lib.delayable.tasks import delayable

from authentication import OAuthAuthentication


log = logging.getLogger('s')
tasty_log = logging.getLogger('django.request.tastypie')


def colorize(colorname, text):
    if curlish:
        return get_color(colorname) + text + ANSI_CODES['reset']
    return text


def formatted_json(json):
    if curlish:
        print_formatted_json(json)
        return
    print json


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


class APIClient(Client):

    def _process(self, kwargs):
        if not 'content_type' in kwargs:
            kwargs['content_type'] = 'application/json'
        if 'data' in kwargs and kwargs['content_type'] == 'application/json':
            kwargs['data'] = json.dumps(kwargs['data'])
        return kwargs

    def get_with_body(self, *args, **kwargs):
        # The Django test client automatically serializes data, not allowing
        # you to do a GET with a body. We want to be able to do that in our
        # tests.
        return super(APIClient, self).post(*args, REQUEST_METHOD='GET',
                                           **self._process(kwargs))

    def post(self, *args, **kwargs):
        return super(APIClient, self).post(*args, **self._process(kwargs))

    def put(self, *args, **kwargs):
        return super(APIClient, self).put(*args, **self._process(kwargs))

    def patch(self, *args, **kwargs):
        return super(APIClient, self).put(*args, REQUEST_METHOD='PATCH',
                                          **self._process(kwargs))


class APITest(test_utils.TestCase):
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
        and ensure that hitting those produces a 405. Otherwise the test will
        fail.
        """
        verbs = ['get', 'post', 'put', 'delete', 'patch']
        # TODO(andym): get patch in here.
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
    severity = kw.get('severity', g('CEF_DEFAULT_SEVERITY', 5))
    cef_kw = {'msg': msg, 'signature': request.get_full_path(),
              'config': {
                  'cef.product': 'Solitude',
                  'cef.vendor': g('CEF_VENDOR', 'Mozilla'),
                  'cef.version': g('CEF_VERSION', '0'),
                  'cef.device_version': g('CEF_DEVICE_VERSION', '0'),
                  'cef.file': g('CEF_FILE', 'syslog'),
              }
        }
    _log_cef(msg, severity, request.META.copy(), **cef_kw)


def handle_500(resource, request, exception):
    # Print some nice 500 errors back to the clients if not in debug mode.
    tb = traceback.format_tb(sys.exc_traceback)
    tasty_log.error('%s: %s %s\n%s' % (request.path,
                        exception.__class__.__name__, exception,
                        '\n'.join(tb)),
                    extra={'status_code': 500, 'request': request})
    data = {
        'error_message': str(exception),
        'error_code': getattr(exception, 'id',
                              exception.__class__.__name__),
        'error_data': getattr(exception, 'data', {})
    }
    # We'll also cef log any errors.
    log_cef(str(exception), request, severity=3)
    serialized = resource.serialize(request, data, 'application/json')
    return http.HttpApplicationError(content=serialized,
                content_type='application/json; charset=utf-8')


class BaseResource(object):

    def form_errors(self, forms):
        errors = {}
        if not isinstance(forms, list):
            forms = [forms]
        for f in forms:
            if isinstance(f.errors, list):  # Cope with formsets.
                for e in f.errors:
                    errors.update(e)
                continue
            errors.update(dict(f.errors.items()))

        response = http.HttpBadRequest(json.dumps(errors),
                                       content_type='application/json')
        raise ImmediateHttpResponse(response=response)

    def dehydrate(self, bundle):
        bundle.data['resource_pk'] = bundle.obj.pk
        return super(BaseResource, self).dehydrate(bundle)

    def _handle_500(self, request, exception):
        return handle_500(self, request, exception)

    def deserialize(self, request, data, format='application/json'):
        result = (super(BaseResource, self)
                                .deserialize(request, data, format=format))
        if settings.DUMP_REQUESTS:
            formatted_json(result)
        return result

    def dispatch(self, request_type, request, **kw):
        method = request.META['REQUEST_METHOD']
        delay = request.META.get('HTTP_SOLITUDE_ASYNC', False)
        if delay:
            # Only do async on these requests.
            if method not in ['PATCH', 'POST', 'PUT']:
                raise ImmediateHttpResponse(response=
                        http.HttpMethodNotAllowed())

            # Create a delayed dispatch.
            uid = str(uuid.uuid4())
            # We only need a subset of meta.
            whitelist = ['PATH_INFO', 'REQUEST_METHOD', 'QUERY_STRING']
            meta = dict([k, request.META[k]] for k in whitelist)
            # Celery could magically serialise some of this, but I don't
            # trust it that much.
            delayable.delay(self.__class__.__module__, self.__class__.__name__,
                            request_type, meta, request.body, kw, uid)
            content = json.dumps({'replay': '/delay/replay/%s/' % uid,
                                  'result': '/delay/result/%s/' % uid})
            return http.HttpResponse(content, status=202,
                                     content_type='application/json')

        # Log the call with CEF and logging.
        if settings.DUMP_REQUESTS:
            print colorize('brace', method), request.get_full_path()
        else:
            log.info('%s %s' % (colorize('brace', method),
                                request.get_full_path()))

        msg = '%s:%s' % (kw.get('api_name', 'unknown'),
                         kw.get('resource_name', 'unknown'))
        log_cef(msg, request)

        return super(BaseResource, self).dispatch(request_type, request, **kw)

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

            if not field_name in self.fields:
                # Don't just ignore this. Tell the world. Shame I have to
                # override all this, just to do this.
                raise InvalidFilterError('Not a valid filtering field: %s'
                                         % field_name)

            if len(filter_bits) and filter_bits[-1] in QUERY_TERMS.keys():
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
            qs_filter = "%s%s%s" % (db_field_name, LOOKUP_SEP, filter_type)
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
            except BaseResource.DoesNotExist:
                pass
        return super(BaseResource, self).is_valid(bundle, request)

    def deserialize_body(self, request):
        # Trying to standardize on JSON in the body for most things if we
        # can. Similar to elastic search. Retaining query string for tastypie
        # record filtering.
        data = request.raw_post_data
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


class Resource(BaseResource, TastyPieResource):

    class Meta:
        always_return_data = True
        authentication = OAuthAuthentication()
        authorization = Authorization()


class ModelResource(BaseResource, TastyPieModelResource):

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
    objects = ManagerBase()

    class Meta:
        abstract = True
        ordering = ('-created',)

    def reget(self):
        return self.__class__.objects.get(pk=self.pk)


def invert(data):
    """
    Helper to turn a dict of constants into a choices tuple.
    """
    return [(v, k) for k, v in data.items()]
