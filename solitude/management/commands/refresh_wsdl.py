import os

from django.conf import settings
from django.core.management.base import BaseCommand

import requests

root = os.path.join(settings.ROOT, 'lib', 'bango', 'wsdl')
sources = {
    'prod': [
        ('https://webservices.bango.com/mozillaexporter/?WSDL',
         'mozilla_exporter.wsdl'),
        ('https://webservices.bango.com/billingconfiguration/?WSDL',
         'billing_configuration.wsdl'),
    ],
    'test': [
        ('https://webservices.test.bango.org/mozillaexporter/?WSDL',
         'mozilla_exporter.wsdl'),
        ('https://webservices.test.bango.org/billingconfiguration/?WSDL',
         'billing_configuration.wsdl'),
    ]
}


class Command(BaseCommand):
    help = "Refresh the WSDLs."

    def handle(self, *args, **kw):
        for dir, paths in sources.items():
            for src, filename in paths:
                dest = os.path.join(root, dir, filename)
                top = os.path.dirname(dest)
                if not os.path.exists(top):
                    os.makedirs(top)
                print 'Getting', src
                open(dest, 'w').write(requests.get(src).text)
                print '...written to', dest
