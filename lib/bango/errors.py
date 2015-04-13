class BangoError(Exception):

    def __init__(self, id, message):
        self.id = id
        self.message = message

    def __str__(self):
        return u'%s: %s' % (self.id, self.message)


class AuthError(BangoError):

    """We've got the settings wrong on our end."""


class BangoFormError(BangoError):

    """Something in the data we passed caused an error in the bango end."""


class ProxyError(Exception):

    """The proxy returned something we didn't like."""
