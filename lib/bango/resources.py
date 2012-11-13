from django.conf import settings
from django.core.urlresolvers import reverse

from suds import client as sudsclient

from lib.sellers.models import Seller, SellerBango
from solitude.base import Cached, Resource as BaseResource

from .forms import PackageForm


class Resource(BaseResource):

    class Meta(BaseResource.Meta):
        object_class = Cached

    def get_resource_uri(self, bundle):
        return reverse('api_dispatch_detail',
                        kwargs={'api_name': 'bango',
                                'resource_name': self._meta.resource_name,
                                'pk': bundle.obj.pk})

    def populate(self, obj, data):
        # TODO(Kumar) refactor this to use BangoProxy (bug 812661).
        obj.username = settings.BANGO_USERNAME
        obj.password = settings.BANGO_PASSWORD
        for k, v in data.iteritems():
            setattr(obj, k, v)

    def client(self):
        return sudsclient.Client(self.wsdl)  # Cached internally by suds.


class ExporterResource(Resource):
    wsdl = settings.BANGO_EXPORTER_WSDL


class PackageResource(ExporterResource):

    class Meta(Resource.Meta):
        resource_name = 'package'
        list_allowed_methods = ['post']

    def obj_create(self, bundle, request, **kw):
        form = PackageForm(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        client = self.client()
        package = client.factory.create('CreatePackageRequest')
        self.populate(package, bundle.data)
        resp = client.service.CreatePackage(package)

        data = {'seller_pk': None,
                'seller_bango_pk': None,
                'response_code': resp.responseCode,
                'response_message': resp.responseMessage}

        if data['response_code'] == 'OK':
            seller = Seller.objects.create(uuid='bango:%s' % resp.packageId)
            seller_bango = SellerBango.objects.create(
                seller=seller,
                package_id=resp.packageId,
                admin_person_id=resp.adminPersonId,
                support_person_id=resp.supportPersonId,
                finance_person_id=resp.financePersonId)
            data['seller_pk'] = seller.pk
            data['seller_bango_pk'] = seller_bango.pk

        bundle.data = data
        return bundle


class BillingConfigResource(Resource):
    wdsl = settings.BANGO_BILLING_CONFIG_WSDL
