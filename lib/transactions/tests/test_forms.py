from datetime import datetime, timedelta

from mock import patch

from django.conf import settings
from django.core.exceptions import ValidationError

from lib.transactions import constants
from lib.transactions.forms import check_status
from solitude.base import APITest


@patch.object(settings, 'TRANSACTION_LOCKDOWN', 60)
class TestModel(APITest):

    @patch.object(settings, 'TRANSACTION_LOCKDOWN', 60)
    def test_lockdown(self):
        check_status({'created': datetime.now() - timedelta(seconds=55),
                      'status': constants.STATUS_CHECKED},
                     {'status': constants.STATUS_COMPLETED})
        with self.assertRaises(ValidationError):
            check_status({'created': datetime.now() - timedelta(seconds=65)},
                         {})

    def test_failed(self):
        with self.assertRaises(ValidationError):
            check_status({'created': datetime.now(), 'status':
                          constants.STATUS_FAILED},
                         {'status': constants.STATUS_PENDING})

    def test_checked(self):
        with self.assertRaises(ValidationError):
            check_status({'created': datetime.now(), 'status':
                          constants.STATUS_CHECKED},
                         {'status': constants.STATUS_PENDING})
        check_status({'created': datetime.now(),
                      'status': constants.STATUS_CHECKED},
                     {'status': constants.STATUS_COMPLETED})
