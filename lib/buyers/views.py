from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view
from rest_framework.response import Response

from lib.buyers.forms import PinForm
from lib.buyers.models import Buyer
from lib.buyers.serializers import (
    BuyerSerializer, ConfirmedSerializer, VerifiedSerializer)
from solitude.base import log_cef, NonDeleteModelViewSet
from solitude.errors import FormError
from solitude.logger import getLogger

log = getLogger('s.buyer')


class BuyerViewSet(NonDeleteModelViewSet):
    queryset = Buyer.objects.all()
    serializer_class = BuyerSerializer
    filter_fields = ('uuid', 'active')


@api_view(['POST'])
def confirm_pin(request):
    form = PinForm(data=request.DATA)

    if form.is_valid():
        buyer = form.cleaned_data['buyer']
        confirmed = False

        if buyer.pin == form.cleaned_data['pin']:
            buyer.pin_confirmed = True
            confirmed = True
            buyer.save()
        else:
            buyer.pin_confirmed = False
            buyer.save()

        output = ConfirmedSerializer(instance=buyer, confirmed=confirmed)
        return Response(output.data)

    raise FormError(form.errors)


@api_view(['POST'])
def verify_pin(request):
    form = PinForm(data=request.DATA)

    if form.is_valid():
        buyer = form.cleaned_data['buyer']
        valid = False
        locked = False

        if buyer.pin_confirmed:
            # Note that the incr_lockout and clear_lockout methods
            # trigger saves on the object. You should not do a save
            # in this view as well for fear of stomping on the save
            # caused by those methods.
            if buyer.locked_out:
                log_cef('Attempted access to locked out account: %s'
                        % buyer.uuid, request, severity=1)
                locked = True

            else:
                valid = buyer.pin == form.cleaned_data['pin']
                if not valid:
                    locked = buyer.incr_lockout()
                    if locked:
                        locked = True
                        log_cef('Locked out account: %s' % buyer.uuid,
                                request, severity=1)
                else:
                    buyer.clear_lockout(clear_was_locked=True)

        output = VerifiedSerializer(instance=buyer, valid=valid, locked=locked)
        return Response(output.data)

    raise FormError(form.errors)


@api_view(['POST'])
def reset_confirm_pin(request):
    form = PinForm(data=request.DATA)
    if form.is_valid():
        buyer = form.cleaned_data['buyer']
        confirmed = False

        if buyer.locked_out:
            log_cef('Attempted access to locked out account: %s'
                    % buyer.uuid, request, severity=1)

        else:
            if buyer.new_pin == form.cleaned_data['pin']:
                buyer.pin = form.cleaned_data['pin']
                buyer.new_pin = None
                buyer.needs_pin_reset = False
                buyer.pin_confirmed = True
                buyer.pin_was_locked_out = False
                buyer.save()
                confirmed = True

        output = ConfirmedSerializer(instance=buyer, confirmed=confirmed)
        return Response(output.data)

    raise FormError(form.errors)


@api_view(['POST'])
def close(request, pk):
    buyer = get_object_or_404(Buyer, pk=pk, active=True)
    log.info('Closing account for: {}'.format(buyer.pk))
    buyer.close()
    return Response(status=204)
