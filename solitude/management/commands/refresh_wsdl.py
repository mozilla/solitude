import os

from django.conf import settings
from django.core.management.base import BaseCommand

import requests

root = os.path.join(settings.ROOT, 'lib/bango/wsdl')
sources = [
    ('https://webservices.bango.com/mozillaexporter/?WSDL',
     os.path.join(root, 'mozilla_exporter.wsdl')),
    ('https://webservices.bango.com/billingconfiguration/?WSDL',
     os.path.join(root, 'billing_configuration.wsdl')),
]


class Command(BaseCommand):
    help = "Refresh the WSDL."

    def handle(self, *args, **kw):
        for src, dest in sources:
            print 'Getting', src
            open(dest, 'w').write(requests.get(src).text)
            print '...written to', dest
