# test_utils picks this file up for testing.
import os
filename = os.path.join(os.path.dirname(__file__),
                  'vendor-local/django-mysql-aesfield/aesfield/sample.key')
AES_KEYS = {
    'buyerpaypal:key': filename,
    'sellerpaypal:id': filename,
    'sellerpaypal:token': filename,
    'sellerpaypal:secret': filename,
}
