#
# %(header)s
#

MAILTO=amo-developers@mozilla.org

HOME=/tmp

# Every 10 minutes run the stats log for today so we can see progress.
*/10 * * * * %(django)s log --type=stats --today

# Once per day, generate stats log for yesterday so that we have a final log.
05 0 * * * %(django)s log --type=stats

# Once per day, generate revenue log for monolith for yesterday.
10 0 * * * %(django)s log --type=revenue

# Once per day, clean statuses older than BANGO_STATUSES_LIFETIME setting.
35 0 * * * %(django)s clean_statuses

MAILTO=root
