from django.core.urlresolvers import reverse

from lib.sellers.models import Seller, SellerBango
from solitude.base import Cached, ModelResource

from .client import get_client
from .forms import PackageForm, UpdateForm


class PackageResource(ModelResource):

    class Meta(ModelResource.Meta):
        queryset = SellerBango.objects.all()
        list_allowed_methods = ['post']
        allowed_methods = ['get', 'patch']
        resource_name = 'package'

    def obj_create(self, bundle, request, **kw):
        """
        Create a SellerBango record, which just passes the data
        through to Bango and then stores the result here.
        """
        form = PackageForm(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        resp = get_client().CreatePackage(bundle.data)

        # TODO: move this out, so that the seller is sent in the request.
        seller = Seller.objects.create(uuid='bango:%s' % resp.packageId)
        seller_bango = SellerBango.objects.create(
                seller=seller,
                package_id=resp.packageId,
                admin_person_id=resp.adminPersonId,
                support_person_id=resp.supportPersonId,
                finance_person_id=resp.financePersonId)
        bundle.obj = seller_bango
        return bundle

    def obj_update(self, bundle, request, **kw):
        """
        Update the Bango records and then our record. We'll assume that
        any data that is sent in the patch is optional, if ignored, we won't
        update. We also don't know what the old value is, we just assume if
        its there its an update.
        """
        form = UpdateForm(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        fields = [(k, v) for k, v in form.cleaned_data.items() if v]
        if fields:
            client = get_client()
            # Perhaps this should move to the form. But not sure how many of
            # these we are going to have, so make a loop that's easy to add
            # to.
            methods = {'supportEmailAddress':
                       # The client method to call. Then the model field to
                       # change on the SellerBango object.
                       ['UpdateSupportEmailAddress', 'support_person_id'],
                       'financeEmailAddress':
                       ['UpdateFinancialEmailAddress', 'finance_person_id']}
            for key, value in fields:
                data = {'packageId': bundle.obj.package_id,
                        'emailAddress': value}
                result = getattr(client, methods[key][0])(data)
                setattr(bundle.obj, methods[key][1], result.personId)
            bundle.obj.save()

        return bundle

