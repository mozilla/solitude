from django import forms
from lib.buyers.models import Buyer


class PreapprovalValidation(forms.Form):
    start = forms.DateField()
    end = forms.DateField()
    return_url = forms.URLField()
    cancel_url = forms.URLField()
    uuid = forms.ModelChoiceField(queryset=Buyer.objects.all(),
                                  to_field_name='uuid')

    def args(self):
        return [self.cleaned_data.get(k) for k in
                ('start', 'end', 'return_url', 'cancel_url')]
