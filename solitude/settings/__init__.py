from .base import *  # flake8: noqa
try:
    from .local import *  # flake8: noqa
except ImportError:
    print 'No local.py imported, skipping.'
