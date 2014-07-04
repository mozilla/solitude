from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def validate_settings():
    """
    Validate that if not in DEBUG mode, key settings have been changed.
    """
    if settings.DEBUG:
        return

    # Things that values must not be.
    for key, value in [
            ('SECRET_KEY', 'please change this'),
            ('HMAC_KEYS', {'2011-01-01': 'please change me'})]:
        if getattr(settings, key) == value:
            raise ImproperlyConfigured('{0} must be changed from default'
                                       .format(key))

    for key, value in settings.AES_KEYS.items():
        if value == 'solitude/settings/sample.key':
            raise ImproperlyConfigured('AES_KEY {0} must be changed from '
                                      'default'.format(key))
