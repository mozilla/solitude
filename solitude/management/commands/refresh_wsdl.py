import os

from django.conf import settings
from django.core.management.base import BaseCommand

import requests

from lib.bango.constants import WSDL_MAP

root = os.path.join(settings.ROOT, 'lib', 'bango', 'wsdl')


class Command(BaseCommand):
    help = "Refresh the WSDLs."

    def handle(self, *args, **kw):
        for dir, wsdls in WSDL_MAP.items():
            for wsdl in wsdls.values():
                filename = wsdl['file']
                src = wsdl['url']
                dest = os.path.join(root, dir, filename)
                top = os.path.dirname(dest)
                if not os.path.exists(top):
                    os.makedirs(top)

                print 'Getting', src
                response = requests.get(src, verify=False)
                if response.status_code != 200:
                    print ('...returned a {0}, skipping'
                           .format(response.status_code))
                    continue

                open(dest, 'w').write(response.text)
                print '...written to', dest
