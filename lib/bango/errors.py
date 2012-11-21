class BangoError(Exception):
    def __init__(self, type, message):
        self.type = type
        self.message = message

    def __unicode__(self):
        return u'%s: %s' % (self.type, self.message)


class AuthError(BangoError):
    # We've got the settings wrong on our end.
    pass
