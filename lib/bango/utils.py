import hashlib
import hmac

from aesfield.default import lookup


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
