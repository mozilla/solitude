class BangoError(Exception):
    def __init__(self, id, message):
        self.id = type
        self.message = message

    def __str__(self):
        return u'%s: %s' % (self.id, self.message)


class AuthError(BangoError):
    # We've got the settings wrong on our end.
    pass
