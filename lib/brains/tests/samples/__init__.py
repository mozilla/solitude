import os

from django.conf import settings


def get_sample(name):
    if not name.endswith('.xml'):
        name = name + '.xml'

    path = os.path.join(settings.ROOT, 'lib/brains/tests/samples', name)
    return open(path, 'rb').read()
