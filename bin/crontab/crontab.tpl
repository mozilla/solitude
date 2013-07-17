#
# %(header)s
#

MAILTO=amo-developers@mozilla.org

HOME=/tmp

# once per day, generate stats log and upload to S3
05 0 * * * %(django)s stats_log

# once per day, clean statuses older than BANGO_STATUSES_LIFETIME setting
35 0 * * * %(django)s clean_statuses

MAILTO=root
