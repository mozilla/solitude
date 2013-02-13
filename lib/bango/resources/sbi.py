from tastypie.exceptions import ImmediateHttpResponse
from tastypie import fields
from tastypie.http import HttpNotFound

from cached import SimpleResource

from lib.bango.constants import SBI_ALREADY_ACCEPTED
from lib.bango.errors import BangoFormError
from lib.bango.forms import SBIForm


class SBIAgreement(object):
    pk = 'agreement'

    def __init__(self, text, valid, expires, accepted):
        self.text = text
        self.valid = valid
        self.expires = expires
        self.accepted = accepted


class SBIResource(SimpleResource):
    text = fields.CharField(readonly=True, attribute='text')
    valid = fields.DateField(readonly=True, attribute='valid', null=True)
    expires = fields.DateField(readonly=True, attribute='expires', null=True)
    accepted = fields.DateField(readonly=True, attribute='accepted',
                                null=True)

    class Meta(SimpleResource.Meta):
        resource_name = 'sbi'
        allowed_methods = ['get']
        list_allowed_methods = ['post']

    def obj_create(self, bundle, request, **kwargs):
        form = SBIForm(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        try:
            res = self.client('AcceptSBIAgreement', form.bango_data,
                              raise_on=(SBI_ALREADY_ACCEPTED))
        except BangoFormError, exc:
            if exc.id != SBI_ALREADY_ACCEPTED:
                raise

        res = self.client('GetAcceptedSBIAgreement', form.bango_data)
        seller_bango = form.cleaned_data['seller_bango']
        seller_bango.sbi_expires = res.sbiAgreementExpires
        seller_bango.save()

        bundle.obj = SBIAgreement('', None, res.acceptedSBIAgreement,
                                  res.sbiAgreementExpires)
        return bundle

    def obj_get(self, request, **kwargs):
        # We are expecting the pk to be 'agreement' so that are we not doing a
        # get on a list and all the tastypie baggage that provides.
        if kwargs['pk'] != 'agreement':
            raise ImmediateHttpResponse(response=HttpNotFound())

        data = self.deserialize(request, request.raw_post_data,
                                format='application/json')
        form = SBIForm(data)
        if not form.is_valid():
            raise self.form_errors(form)

        res = self.client('GetSBIAgreement', form.bango_data)
        return SBIAgreement(res.sbiAgreement, res.sbiAgreementValidFrom,
                            None, None)
