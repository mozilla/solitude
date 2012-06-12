from solitude.base import SolitudeResource
from tastypie.validation import FormValidation
from .models import Buyer
from django.forms import ModelForm


class BuyerValidation(ModelForm):

    class Meta:
        model = Buyer


class BuyerResource(SolitudeResource):

    class Meta(SolitudeResource.Meta):
        queryset = Buyer.objects.all()
        fields = ['uuid']
        list_allowed_methods = ['post']
        allowed_methods = ['get']
        resource_name = 'buyer'
        validation = FormValidation(form_class=BuyerValidation)
