from django import forms


class ListField(forms.CharField):

    def clean(self, value):
        if not isinstance(value, list):
            raise forms.ValidationError('Invalid list.')
        return value
