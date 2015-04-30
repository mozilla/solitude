from django.core.urlresolvers import reverse
from django.db import models

from lib.buyers.models import Buyer
from solitude.base import Model


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
        return reverse('braintree:buyer', kwargs={'pk': self.pk})

    def save(self, *args, **kw):
        if not self.pk:
            self.braintree_id = str(self.buyer.pk)
        return super(BraintreeBuyer, self).save(*args, **kw)
