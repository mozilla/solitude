#
# {{ header }}
#

MAILTO=amo-developers@mozilla.org

HOME=/tmp

# once per day
05 0 * * * %(django)s stats_log

MAILTO=root
