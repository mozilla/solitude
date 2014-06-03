from .base import *
try:
    from .local import *
except ImportError:
    print 'No local.py imported, skipping.'
