"""
Deploy this project in dev/stage/production.

Requires commander_ which is installed on the systems that need it.

.. _commander: https://github.com/oremj/commander
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from commander.deploy import task, hostgroups, BadReturnCode
import commander_settings as settings


@task
def create_virtualenv(ctx):
    venv = settings.VIRTUAL_ENV
    if not venv.startswith('/data'):
        # this is just to avoid rm'ing /
        raise Exception('venv must start with /data')

    ctx.local('rm -rf %s' % venv)

    try:
        try:
            ctx.local("virtualenv --distribute --never-download %s" % venv)
        except BadReturnCode:
            # if this is really broken, then the pip install should fail
            pass

        ctx.local("%s/bin/pip install --exists-action=w --no-deps --no-index "
                  "--download-cache=/tmp/pip-cache -f %s "
                  "-r %s/requirements/prod.txt" %
                  (venv, settings.PYREPO, settings.SRC_DIR))
    finally:
        # make sure this always runs
        ctx.local("rm -f %s/lib/python2.6/no-global-site-packages.txt" % venv)
        ctx.local("%s/bin/python /usr/bin/virtualenv --relocatable %s"
                  % (venv, venv))


@task
def update_code(ctx, tag):
    """Update the code to a specific git reference (tag/sha/etc)."""
    with ctx.lcd(settings.SRC_DIR):
        ctx.local('git fetch')
        ctx.local('git reset --hard %s' % tag)
        ctx.local('git submodule sync')
        ctx.local('git submodule update --init --recursive')


@task
def update_locales(ctx):
    """Update a locale directory from SVN.

    Assumes localizations 1) exist, 2) are in SVN, 3) are in SRC_DIR/locale and
    4) have a compile-mo.sh script. This should all be pretty standard, but
    change it if you need to.

    """
    with ctx.lcd(os.path.join(settings.SRC_DIR, 'locale')):
        ctx.local('svn up')
        ctx.local('./compile-mo.sh .')


@task
def update_assets(ctx):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("%s manage.py collectstatic --noinput" % settings.PYTHON)
        # LANG=en_US.UTF-8 is sometimes necessary for the YUICompressor.
        ctx.local('LANG=en_US.UTF8 %s manage.py compress_assets'
                  % settings.PYTHON)


@task
def update_db(ctx):
    """Update the database schema, if necessary.

    Uses schematic by default. Change to south if you need to.

    """
    if not getattr(settings, 'IS_PROXY', False):
        with ctx.lcd(settings.SRC_DIR):
            ctx.local("%s %s/bin/schematic migrations" %
                      (settings.PYTHON, settings.VIRTUAL_ENV))


@task
def checkin_changes(ctx):
    """Use the local, IT-written deploy script to check in changes."""
    ctx.local(settings.DEPLOY_SCRIPT)


@hostgroups(settings.WEB_HOSTGROUP,
            remote_kwargs={'ssh_key': settings.SSH_KEY})
def deploy_app(ctx):
    """Call the remote update script to push changes to webheads."""
    ctx.remote(settings.REMOTE_UPDATE_SCRIPT)
    ctx.remote('service %s reload' % settings.GUNICORN)


@task
def update_info(ctx):
    """Write info about the current state to a publicly visible file."""
    with ctx.lcd(settings.SRC_DIR):
        ctx.local('date')
        ctx.local('git branch')
        ctx.local('git log -3')
        ctx.local('git status')
        ctx.local('git submodule status')


@task
def disable_cron(ctx):
    ctx.local("rm -f /etc/cron.d/%s" % settings.CRON_NAME)


@task
def install_cron(ctx):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local('%s ./bin/update/gen-crons.py '
                  '-p %s -u apache -w %s > /etc/cron.d/.%s' %
                  (settings.PYTHON, settings.PYTHON, settings.SRC_DIR,
                   settings.CRON_NAME))

        ctx.local('mv /etc/cron.d/.%s /etc/cron.d/%s' % (settings.CRON_NAME,
                                                         settings.CRON_NAME))


@task
def pre_update(ctx, ref=settings.UPDATE_REF):
    """Update code to pick up changes to this file."""
    disable_cron()
    update_code(ref)
    update_info()


@task
def post_update(ctx):
    install_cron()
    with ctx.lcd(settings.SRC_DIR):
        ctx.local('%s manage.py statsd_ping --key=update' % settings.PYTHON)


@task
def update(ctx):
    update_db()


@task
def deploy(ctx):
    checkin_changes()
    deploy_app()


@task
def update_site(ctx, tag):
    """Update the app to prep for deployment."""
    pre_update(tag)
    create_virtualenv()
    update()
    post_update()
