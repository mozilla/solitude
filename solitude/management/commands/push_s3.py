import os
import sys
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand

import boto
from boto.s3.key import Key


def push(source):
    if not all(settings.S3_AUTH.values() + [settings.S3_BUCKET,]):
        print 'Settings incomplete.'
        sys.exit(1)

    dest = os.path.basename(source)
    conn = boto.connect_s3(settings.S3_AUTH['key'],
                           settings.S3_AUTH['secret'])
    bucket = conn.get_bucket(settings.S3_BUCKET)
    k = Key(bucket)
    k.key = dest
    k.set_contents_from_filename(source)
    print 'Uploaded: {0} to: {1}'.format(source, dest)


class Command(BaseCommand):
    help = 'Push a file to S3'
    option_list = BaseCommand.option_list + (
        make_option('--file', action='store', type='string', dest='file',
                    default=''),
    )

    def handle(self, *args, **options):
        source = options['file']
        if not source or not os.path.exists(source):
            print 'File not found: {0}'.format(source)
            sys.exit(1)

        push(source)
