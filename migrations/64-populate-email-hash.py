from lib.buyers.models import Buyer
from solitude.logger import getLogger

log = getLogger(__name__)


def run():
    for buyer in Buyer.objects.values('id', 'email'):
        if not buyer['email']:
            continue

        log.info('Updating email_hash for {}'.format(buyer['id']))
        Buyer.objects.get(pk=buyer['id']).save()
