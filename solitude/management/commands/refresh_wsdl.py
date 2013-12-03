import os

from django.conf import settings
from django.core.management.base import BaseCommand

import requests


class Command(BaseCommand):
    help = "Refresh the WSDLs."

    def handle(self, *args, **kw):
        for dir, paths in settings.BANGO_WSDL.items():
            for src, filename in paths:
                dest = os.path.join(settings.BANGO_WSDL_DIRECTORY,
                                    dir, filename)
                top = os.path.dirname(dest)
                if not os.path.exists(top):
                    os.makedirs(top)
                print 'Getting', src
                open(dest, 'w').write(requests.get(src).text)
                print '...written to', dest
