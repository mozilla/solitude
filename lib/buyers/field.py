import hashlib
import hmac

from django.conf import settings
from django.contrib.auth.hashers import (check_password, get_hasher,
                                         make_password)
from django.db.models import CharField, SubfieldBase


class HashFieldBase(CharField):

    __metaclass__ = SubfieldBase

    def __init__(self, max_length=255, *args, **kwargs):
        # Longer than the average hash, should generally be more than enough.
        super(HashFieldBase, self).__init__(
            max_length=max_length, *args, **kwargs)

    def get_prep_value(self, value, prepared=False):
        if not prepared and value:
            if not getattr(self, 'salt', False):
                self.salt = get_hasher('default').salt()
            # Check that it isn't already hashed so we don't double hash. This
            # is an issue because the value passed is the value returned
            # to_python() unless you are doing a .update() in which case
            # to_python()  is not called and the value is passed in raw.
            if not isinstance(value, HashedData):
                value = self._hash(value, salt=self.salt)
            self.salt = False  # dump salt after saving.
        return value

    def to_python(self, value):
        if isinstance(value, HashedData):
            return value
        if value == '' or value is None:
            return HashedData('')
        if not isinstance(value, (str, unicode)):
            raise ValueError('HashField only takes str or unicode.')
        hasher = get_hasher('default')
        # Check to see if this is a hash already (likely loaded from the DB),
        # if not then we need to hash it and save the salt so later when we try
        # to save the hash, the same value we see is what is put in the DB.
        if not value.startswith(hasher.algorithm):
            self.salt = hasher.salt()
            value = self._hash(value, salt=self.salt)
        return HashedData(value)


class HashField(HashFieldBase):

    def get_prep_lookup(self, *args, **kw):
        raise NotImplemented('Looking up by hash is not supported')

    def _hash(self, value, salt=None):
        return make_password(value, salt)


class ConsistentSigField(HashFieldBase):

    """
    Like the HashField, but is always a consistent value to allow lookups
    on the field.
    """

    def get_prep_lookup(self, *args, **kw):
        return super(CharField, self).get_prep_lookup(*args, **kw)

    def _hash(self, value, salt=None):
        """
        Hash the value with hmac, using sha256. This ignores values of
        salt, so that the hash can be consistent.
        """
        if not value:
            return ''
        if value.startswith('consistent:'):
            return value
        key_id = max(settings.HMAC_KEYS.keys())
        key_value = settings.HMAC_KEYS[key_id]
        res = hmac.new(key_value, value, hashlib.sha256).hexdigest()
        return 'consistent:' + res


class HashedData(object):

    def __init__(self, value):
        self.value = value

    def check(self, other):
        if self.value == '':
            return False
        if self.value and not other:
            # We can be pretty sure these wont match, exit quickly.
            return False
        return check_password(other, self.value)

    def __eq__(self, other):
        return self.check(other)

    def __unicode__(self):
        return self.value

    def __str__(self):
        return str(self.__unicode__())

    def __repr__(self):
        return '<HashedData: "%s">' % self.value if self.value else 'unset'

    def __len__(self):
        return len(self.value)
