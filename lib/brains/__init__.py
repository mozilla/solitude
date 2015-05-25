# Called brains, because braintree is a python module for interacting with
# braintree and was already taken.

# Potential work around for https://bugs.python.org/issue7980,
# Braintree uses strptime in their library and I was seeing intermittent
# errors on parsing webhooks:
#
#  File "...braintree/util/parser.py", line 42, in __convert_to_datetime
#    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
# AttributeError: _strptime

import _strptime  # noqa
