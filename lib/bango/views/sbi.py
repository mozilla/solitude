from rest_framework.decorators import api_view
from rest_framework.response import Response

from lib.bango.constants import SBI_ALREADY_ACCEPTED
from lib.bango.errors import BangoAnticipatedError
from lib.bango.serializers import EasyObject, SBISerializer, SellerBangoOnly
from lib.bango.utils import terms
from lib.bango.views.base import BangoResource


@api_view(['POST', 'GET'])
def sbi(request):
    view = BangoResource()
    if request.method.upper() == 'GET':
        return sbi_get(view, request)
    return sbi_post(view, request)


def sbi_post(view, request):
    serial = SellerBangoOnly(data=request.DATA)
    if not serial.is_valid():
        return Response(serial.errors, status=400)

    data = {'packageId': serial.object['seller_bango'].package_id}
    try:
        res = view.client('AcceptSBIAgreement', data,
                          raise_on=[SBI_ALREADY_ACCEPTED])
    except BangoAnticipatedError, exc:
        if exc.id != SBI_ALREADY_ACCEPTED:
            raise

    res = view.client('GetAcceptedSBIAgreement', data)
    seller_bango = serial.object['seller_bango']
    seller_bango.sbi_expires = res.sbiAgreementExpires
    seller_bango.save()

    obj = EasyObject(
        text='',
        valid=None,
        accepted=res.acceptedSBIAgreement,
        expires=res.sbiAgreementExpires
    )
    return Response(SBISerializer(obj).data)


def sbi_get(view, request):
    serial = SellerBangoOnly(data=request.DATA)
    if not serial.is_valid():
        return Response(serial.errors, status=400)

    data = {'packageId': serial.object['seller_bango'].package_id}
    res = view.client('GetSBIAgreement', data)
    obj = EasyObject(
        text=terms(res.sbiAgreement),
        valid=res.sbiAgreementValidFrom,
        accepted=None,
        expires=None
    )
    return Response(SBISerializer(obj).data)
