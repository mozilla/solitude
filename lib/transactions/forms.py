from django import forms

from django_paranoia.forms import ParanoidForm

from .constants import STATUSES


class UpdateForm(ParanoidForm):
    notes = forms.CharField(required=False)
    status = forms.ChoiceField(choices=[(v, v) for v in STATUSES.values()],
                               required=False)

    def clean(self):
        keys = set(self.data.keys()).difference(set(self.fields.keys()))
        if keys:
            raise forms.ValidationError('Cannot alter fields: %s' %
                                        ', '.join(keys))
        return self.cleaned_data
