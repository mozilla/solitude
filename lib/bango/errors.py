class BangoError(Exception):

    def __init__(self, id, message):
        self.id = id
        self.message = message

    def __str__(self):
        return u'%s: %s' % (self.id, self.message)


class AuthError(BangoError):

    """We've got the settings wrong on our end."""


class BangoAnticipatedError(BangoError):

    """
    Something in the data we passed caused an error in the Bango end.

    This error is to denote that the error is going to be raised, but
    will be anticipated in some circumstances. This allows it to be caught
    and handled appropriately.
    """


class BangoUnanticipatedError(BangoError):

    """
    Something in the data we passed caused Bango to return an error
    of not OK.

    This error is to denote that the error is going to be raised, but
    will be NOT anticipated. This allows it to be caught
    and handled appropriately.
    """


class BangoImmediateError(Exception):

    """
    Something in the data we passed caused an error in Bango and rather
    than let it get trapped somewhere, we want to raise this immediately.
    """


class ProxyError(Exception):

    """The proxy returned something we didn't like."""


class ProcessError(Exception):

    def __init__(self, response):
        self.response = response
