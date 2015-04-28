from rest_framework import serializers


class BraintreeSerializer(serializers.Serializer):

    def __init__(self, instance=None):
        self.object = instance

    @property
    def data(self):
        return dict([k, getattr(self.object, k)] for k in self.fields)


class CustomerSerializer(BraintreeSerializer):
    fields = ['id', 'created_at', 'updated_at']
