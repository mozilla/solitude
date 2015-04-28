from django import forms


class BuyerForm(forms.Form):
    uuid = forms.CharField(max_length=255)
