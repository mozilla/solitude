from rest_framework.response import Response

from ..client import response_to_dict
from ..constants import INVALID_PERSON, VAT_NUMBER_DOES_NOT_EXIST
from ..errors import BangoAnticipatedError, ProcessError
from ..forms import (FinanceEmailForm, PackageForm,
                     SupportEmailForm, UpdateAddressForm,
                     VatNumberForm)
from lib.bango.serializers import PackageSerializer, SellerBangoSerializer
from lib.bango.views.base import BangoResource
from lib.sellers.models import SellerBango
from solitude.base import NonDeleteModelViewSet


class PackageViewSet(NonDeleteModelViewSet, BangoResource):
    queryset = SellerBango.objects.filter()
    serializer_class = SellerBangoSerializer

    error_lookup = {
        'INVALID_COUNTRYISO': 'countryIso',
        'INVALID_CURRENCYISO': 'currencyIso',
        'INVALID_URL': 'homePageURL',
    }

    def create(self, request, *args, **kw):
        """
        Create a SellerBango record, which just passes the data
        through to Bango and then stores the result here.
        """

        try:
            serial, form = self.process(
                serial_class=PackageSerializer,
                form_class=PackageForm,
                request=request)
        except ProcessError, exc:
            return exc.response

        resp = self.client('CreatePackage', form.bango_data)

        seller_bango = SellerBango.objects.create(
            seller=serial.object['seller'],
            package_id=resp.packageId,
            admin_person_id=resp.adminPersonId,
            support_person_id=resp.supportPersonId,
            finance_person_id=resp.financePersonId
        )

        new_serial = SellerBangoSerializer(seller_bango)
        return Response(new_serial.data, status=201)

    def update(self, request, *args, **kw):
        """
        Update the Bango records and then our record. We'll assume that
        any data that is sent in the patch is optional, if ignored, we won't
        update. We also don't know what the old value is, we just assume if
        its there its an update.
        """
        if kw.get('partial') is not True:
            return Response(status=405)

        # These four forms are just that, forms that contain standard fields
        # with nothing linking to another object. Using forms seems appropriate
        # here instead of a serializer.
        #
        obj = self.get_object()
        data = request.DATA
        forms = [FinanceEmailForm(data), SupportEmailForm(data),
                 UpdateAddressForm(data), VatNumberForm(data)]

        for form in forms:
            if not form.is_valid():
                return self.form_errors(form)

        for form in forms:
            data = form.bango_data
            keys = form.bango_meta
            data['packageId'] = obj.package_id
            try:
                result = self.client(keys['method'], data,
                                     raise_on=keys.get('raise_on', None))
            except BangoAnticipatedError, exc:
                # We don't know the persons email account, we only
                # know that Bango might not like it if its unchanged.
                if exc.id not in (INVALID_PERSON, VAT_NUMBER_DOES_NOT_EXIST):
                    raise
            else:
                if keys.get('to_field'):
                    # Only change the model in some cases.
                    setattr(obj, keys.get('to_field'),
                            getattr(result, keys.get('from_field')))

        obj.save()
        new_serial = SellerBangoSerializer(obj).data.copy()
        new_serial.update(form.cleaned_data)
        return Response(new_serial, status=201)

    def retrieve(self, request, *args, **kw):
        """
        Retrive the seller bango data, but if a 'full' is specified,
        get the package from bango and include that in the full
        attribute.
        """
        self.object = self.get_object()
        data = self.get_serializer(self.object).data
        data['full'] = {}
        if request.DATA.get('full'):
            data['full'] = response_to_dict(
                self.client(
                    'GetPackage',
                    {'packageId': self.object.package_id}
                )
            )
        return Response(data)
