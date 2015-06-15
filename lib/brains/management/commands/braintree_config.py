from decimal import Decimal
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from payments_config import sellers
from lib.brains.client import get_client
from lib.sellers.models import Seller, SellerProduct
from solitude.logger import getLogger

log = getLogger('s.brains.management')


def get_or_create_seller(uuid):
    """
    Create a seller in solitude for the product.
    """
    # We'll suffix with the BRAINTREE_MERCHANT_ID so that the seller will
    # change if you change ids, or servers.
    uuid = uuid + '-' + settings.BRAINTREE_MERCHANT_ID
    seller, created = Seller.objects.get_or_create(uuid=uuid)
    log.info('Seller {0}, pk: {1}'
             .format('created' if created else 'exists', seller.pk))
    return seller


def get_or_create_seller_product(external_id, public_id, seller):
    """
    Create a seller product in solitude for each product.
    """
    seller_product, created = SellerProduct.objects.get_or_create(
        external_id=external_id, public_id=public_id, seller=seller)
    log.info('SellerProduct {0}, uuid: {1}'
             .format('created' if created else 'exists', seller_product.pk))
    return seller_product


def product_exists(plans, external_id, amount):
    """
    Check that the product exists in Braintree.
    """
    if external_id not in plans:
        log.warning(
            'The plan: {0} does not exist in Braintree. Plans cannot be '
            'created from the API and must be created from the Braintree '
            'console.'
            .format(external_id))

        raise CommandError('Missing product: {0}'.format(external_id))

    plan = plans[external_id]
    if Decimal(plan.price) != amount:
        log.warning(
            'The plan: {0} in Braintree has a different amount ({1}) from the '
            'configuration file ({2}). It will need to be updated in '
            'Braintree.'
            .format(external_id, plan.price, amount))

        raise CommandError('Different price: {0}'.format(external_id))

    log.info('Plan: {0} exists correctly on Braintree'.format(external_id))


def get_plans(client):
    return dict((p.id, p) for p in client.Plan.all())


class Command(BaseCommand):
    help = 'Creates products in solitude and braintree from configuration.'
    option_list = BaseCommand.option_list + (
        make_option(
            '--path',
            dest='path',
            default='solitude.settings.products',
            help=('Dotted path to the settings file, '
                  'eg: solitude.settings.products')
        ),
    )

    def handle(self, *args, **options):
        client = get_client()
        for seller_name, seller_config in sellers.items():
            log.info('Configuring: {0}'.format(seller_name))
            seller = get_or_create_seller(seller_name)
            plans = get_plans(client)
            # Iterate through each product checking they exist.
            for product in seller_config.products:
                get_or_create_seller_product(
                    external_id=product.id,
                    public_id=product.id,
                    seller=seller
                )
                product_exists(plans, product.id, product.amount)
