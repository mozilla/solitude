import json
import uuid

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse

from rest_framework.exceptions import ParseError
from rest_framework.mixins import (CreateModelMixin, ListModelMixin,
                                   RetrieveModelMixin)
from rest_framework.response import Response
from rest_framework.serializers import HyperlinkedModelSerializer, Serializer
from rest_framework.viewsets import GenericViewSet, ViewSet
from tastypie.exceptions import ImmediateHttpResponse

from lib.bango.models import Status
from lib.bango.forms import CreateBillingConfigurationForm
from lib.bango.constants import STATUS_BAD, STATUS_GOOD
from lib.bango.resources.billing import CreateBillingConfigurationResource
from lib.sellers.models import SellerProductBango
from lib.transactions.constants import SOURCE_BANGO

from solitude.base import CompatRelatedField
from solitude.logger import getLogger

log = getLogger('s.bango')


class StatusSerializer(HyperlinkedModelSerializer):
    seller_product_bango = CompatRelatedField(
        source='seller_product_bango',
        tastypie={'resource_name': 'product', 'api_name': 'bango'},
        view_name='api_dispatch_detail',
        queryset=SellerProductBango.objects.filter())

    class Meta:
        model = Status
        read_only_fields = ('status', 'errors', 'created', 'modified')


class StatusViewSet(CreateModelMixin, ListModelMixin,
                    RetrieveModelMixin, GenericViewSet):
    queryset = Status.objects.filter()
    serializer_class = StatusSerializer

    def post_save(self, obj, created):
        if created:
            log.info('Checking with bango: {0}'
                     .format(obj.seller_product_bango.pk))
            self.check_bango(obj)

    def check_bango(self, obj):
        pk = obj.seller_product_bango.pk
        form = CreateBillingConfigurationForm({
            'seller_product_bango': (
                self.get_serializer().fields['seller_product_bango']
                    .to_native(obj.seller_product_bango)),
            'pageTitle': 'Test of app status',
            'prices': [{'price': 0.99, 'currency': 'USD'}],
            'redirect_url_onerror': 'http://test.mozilla.com/error',
            'redirect_url_onsuccess': 'http://test.mozilla.com/success',
            'transaction_uuid': 'test:status:{0}'.format(uuid.uuid4()),
            'user_uuid': 'test:user:{0}'.format(uuid.uuid4())
        })
        if not form.is_valid():
            log.info('Form not valid: {0}'.format(pk))
            obj.status = STATUS_BAD
            obj.errors = json.dumps({'form.errors': form.errors})
            obj.save()
            raise ParseError

        resource = CreateBillingConfigurationResource()
        try:
            resource.call(form)
        except ImmediateHttpResponse, exc:
            log.info('Bango error: {0}'.format(pk))
            obj.status = STATUS_BAD
            obj.errors = exc.response.content
            obj.save()
            return

        log.info('All good: {0}'.format(pk))
        obj.status = STATUS_GOOD
        obj.save()


class DebugSerializer(Serializer):
    seller_product_bango = CompatRelatedField(
        source='seller_product_bango',
        tastypie={'resource_name': 'product', 'api_name': 'bango'},
        view_name='api_dispatch_detail',
        queryset=SellerProductBango.objects.filter())


class DebugViewSet(ViewSet):

    def list(self, request):
        serializer = DebugSerializer(data=request.DATA)
        if serializer.is_valid():
            obj = serializer.object['seller_product_bango']
            result = {'bango':
                {
                    'environment': settings.BANGO_ENV,
                    'bango_id': obj.bango_id,
                    'package_id': obj.seller_bango.package_id,
                    'last_status': {},
                    'last_transaction': {}
                },
                'solitude': {
                }
            }

            # Show the last status check if present.
            try:
                latest = obj.status.latest()
                result['bango']['last_status'] = {
                    'status': latest.status,
                    'url': reverse('status-detail', kwargs={'pk': latest.pk})
                }
            except ObjectDoesNotExist:
                pass

            # Show the last transaction if present.
            try:
                latest = obj.seller_product.transaction_set.filter(
                            provider=SOURCE_BANGO).latest()
                result['bango']['last_transaction'] = {
                    'status': latest.status,
                    'url': reverse('api_dispatch_detail',
                                   kwargs={'api_name': 'generic',
                                           'resource_name': 'transaction',
                                           'pk': latest.pk})
                }
            except ObjectDoesNotExist:
                pass

            return Response(result, status=200)

        return Response(serializer.errors, status=400)
