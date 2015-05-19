from django.core.urlresolvers import reverse

from rest_framework import serializers

from lib.buyers.constants import BUYER_UUID_ALREADY_EXISTS, FIELD_REQUIRED
from lib.buyers.forms import clean_pin
from lib.buyers.models import Buyer
from solitude.base import BaseSerializer


class BaseBuyerSerializer(BaseSerializer):

    def resource_uri(self, pk):
        return reverse('generic:buyer-detail', kwargs={'pk': pk})


class BuyerSerializer(BaseBuyerSerializer):
    pin_is_locked_out = serializers.BooleanField(
        source='locked_out', read_only=True)
    pin_failures = serializers.IntegerField(read_only=True)
    uuid = serializers.CharField(
        error_messages={'required': FIELD_REQUIRED, 'blank': FIELD_REQUIRED},
    )

    class Meta:
        model = Buyer
        fields = [
            'active', 'email', 'needs_pin_reset', 'new_pin', 'pin',
            'pin_confirmed', 'pin_failures', 'pin_is_locked_out',
            'pin_was_locked_out', 'resource_pk', 'resource_uri', 'uuid'
        ]

    def transform_pin(self, obj, value):
        return bool(value)

    def transform_new_pin(self, obj, value):
        return bool(value)

    def validate_uuid(self, attrs, source):
        value = attrs.get(source)

        qs = Buyer.objects.filter(uuid=value)
        if self.object:
            qs = qs.exclude(pk=self.object.pk)

        if qs.exists():
            raise serializers.ValidationError(BUYER_UUID_ALREADY_EXISTS,
                                              code='not_unique')

        return attrs

    def validate_pin(self, attrs, source):
        # Must get init_data to avoid getting the hashed value of the PIN.
        value = self.init_data.get(source)

        if value:
            clean_pin(value)

        return attrs


class ConfirmedSerializer(BaseBuyerSerializer):
    confirmed = serializers.SerializerMethodField('get_confirmed')

    class Meta:
        model = Buyer
        fields = [
            'confirmed', 'uuid'
        ]

    def __init__(self, *args, **kw):
        self.confirmed = kw.pop('confirmed')
        super(ConfirmedSerializer, self).__init__(*args, **kw)

    def get_confirmed(self, obj):
        return self.confirmed


class VerifiedSerializer(BaseBuyerSerializer):
    locked = serializers.SerializerMethodField('get_locked')
    valid = serializers.SerializerMethodField('get_valid')

    class Meta:
        model = Buyer
        fields = [
            'locked', 'pin', 'uuid', 'valid'
        ]

    def __init__(self, *args, **kw):
        self.valid = kw.pop('valid')
        self.locked = kw.pop('locked')
        super(VerifiedSerializer, self).__init__(*args, **kw)

    def get_valid(self, obj):
        return self.valid

    def get_locked(self, obj):
        return self.locked
