from django.core.urlresolvers import reverse

from lib.sellers.models import Seller, SellerBango
from solitude.base import Cached, Resource as BaseResource

from .client import get_client
from .forms import PackageForm


class Resource(BaseResource):

    class Meta(BaseResource.Meta):
        object_class = Cached

    def get_resource_uri(self, bundle):
        return reverse('api_dispatch_detail',
                        kwargs={'api_name': 'bango',
                                'resource_name': self._meta.resource_name,
                                'pk': bundle.obj.pk})



class PackageResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'package'
        list_allowed_methods = ['post']

    def obj_create(self, bundle, request, **kw):
        form = PackageForm(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        resp = get_client().CreatePackage(bundle.data)

        seller = Seller.objects.create(uuid='bango:%s' % resp.packageId)
        seller_bango = SellerBango.objects.create(
                seller=seller,
                package_id=resp.packageId,
                admin_person_id=resp.adminPersonId,
                support_person_id=resp.supportPersonId,
                finance_person_id=resp.financePersonId)
        bundle.data = {
            'seller_pk': seller.pk,
            'seller_bango_pk': seller_bango.pk
        }
        return bundle
