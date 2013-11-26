import functools
import hashlib
import hmac
import os

from django.conf import settings
from django.template.loader import render_to_string

from aesfield.default import lookup

terms_directory = 'lib/bango/templates/bango/terms'


def sign(msg):
    """
    Sign a message with a Bango key.
    """
    if isinstance(msg, unicode):
        try:
            msg = msg.encode('ascii')
        except UnicodeEncodeError, exc:
            raise TypeError('Cannot sign a non-ascii message. Error: %s'
                            % exc)
    key = lookup(key='bango:signature')
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def verify_sig(sig, msg):
    """
    Verify the signature of a message using a Bango key.
    """
    return str(sig) == sign(msg)


def terms(sbi, language='en-US'):
    """
    Look for a file containing the Bango terms, if not present, it will fall
    back to the en-US.html file.
    """
    full = functools.partial(os.path.join, settings.ROOT, terms_directory)
    templates = (language + '.html', 'en-US.html')
    for template in templates:
        if os.path.exists(full(template)):
            break

    return render_to_string('bango/terms-layout.html',
                            {'sbi': sbi, 'terms': full(template)})
