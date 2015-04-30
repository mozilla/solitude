from django.core.urlresolvers import reverse
from django.db import models

from lib.buyers.models import Buyer
from solitude.base import Model
from solitude.constants import PAYMENT_METHOD_CARD


class BraintreeBuyer(Model):

    """A holder for any braintree specific stuff around the buyer."""
    # Allow us to turn off braintree buyers if we need to.
    active = models.BooleanField(default=True)
    # The specific braintree-id confirming to braintree's requirements.
    # Braintree requires that ids are letters, numbers, -, _. See:
    # https://developers.braintreepayments.com/reference/request/customer/create
    braintree_id = models.CharField(max_length=255, db_index=True, unique=True)
    buyer = models.OneToOneField(Buyer)

    class Meta(Model.Meta):
        db_table = 'buyer_braintree'

    def get_uri(self):
        return reverse('braintree:mozilla:buyer', kwargs={'pk': self.pk})

    def save(self, *args, **kw):
        if not self.pk:
            self.braintree_id = str(self.buyer.pk)
        return super(BraintreeBuyer, self).save(*args, **kw)


class BraintreePaymentMethod(Model):

    """A holder for braintree specific payment method."""

    active = models.BooleanField(default=True)
    braintree_buyer = models.ForeignKey(BraintreeBuyer)
    # An id specific to the provider.
    provider_id = models.CharField(max_length=255)
    # The type of payment method eg: card, paypal or bitcon
    type = models.PositiveIntegerField(choices=(
        (PAYMENT_METHOD_CARD, PAYMENT_METHOD_CARD),
    ))
    # Details about the type, eg Amex, Orange.
    type_name = models.CharField(max_length=255)
    # For credit cards, this is the last 4 numbers, could be a truncated
    # phone number or paypal account for example.
    truncated_id = models.CharField(max_length=255)

    class Meta(Model.Meta):
        db_table = 'braintree_pay_method'

    def get_uri(self):
        return reverse('braintree:mozilla:paymethod-detail',
                       kwargs={'pk': self.pk})
