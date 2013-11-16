"""
Deploy this project in dev/stage/production.

Requires commander_ which is installed on the systems that need it.

.. _commander: https://github.com/oremj/commander
"""

import os.path
from os.path import join as pjoin

from fabric.api import env, execute, lcd, local, task

from fabdeploytools import helpers
import fabdeploytools.envs

import deploysettings as settings

env.key_filename = settings.SSH_KEY
fabdeploytools.envs.loadenv(settings.CLUSTER)

SCL_NAME = getattr(settings, 'SCL_NAME', False)
if SCL_NAME:
    helpers.scl_enable(SCL_NAME)

IS_PROXY = getattr(settings, 'IS_PROXY', False)

ROOT, SOLITUDE = helpers.get_app_dirs(__file__)
VIRTUALENV = pjoin(ROOT, 'venv')
PYTHON = pjoin(VIRTUALENV, 'bin', 'python')


@task
def create_virtualenv():
    venv = VIRTUALENV
    if venv.startswith(pjoin('/data', 'src', settings.CLUSTER)):
        local('rm -rf %s' % venv)

    helpers.create_venv(VIRTUALENV, settings.PYREPO,
                        pjoin(SOLITUDE, 'requirements/prod.txt'))


@task
def update_assets():
    with lcd(SOLITUDE):
        local("%s manage.py collectstatic --noinput" % PYTHON)
        # LANG=en_US.UTF-8 is sometimes necessary for the YUICompressor.
        local('LANG=en_US.UTF8 %s manage.py compress_assets' % PYTHON)


@task
def update_db():
    """Update the database schema, if necessary.

    Uses schematic by default. Change to south if you need to.

    """
    if IS_PROXY:
        return
    with lcd(SOLITUDE):
        local("%s %s/bin/schematic migrations" %
              (PYTHON, VIRTUALENV))


@task
def update_info():
    """Write info about the current state to a publicly visible file."""
    with lcd(SOLITUDE):
        local('date')
        local('git branch')
        local('git log -3')
        local('git status')
        local('git submodule status')


@task
def disable_cron():
    if IS_PROXY:
        return

    local("rm -f /etc/cron.d/%s" % settings.CRON_NAME)


@task
def install_cron(installed_dir):
    if IS_PROXY:
        return

    sol = pjoin(installed_dir, 'solitude')
    python = pjoin(installed_dir, 'venv', 'bin', 'python')
    if SCL_NAME:
        python = "source %s; %s" % (
            os.path.join('/opt/rh', SCL_NAME, 'enable'),
            python
        )

    with lcd(SOLITUDE):
        local('%s ./bin/crontab/gen-crons.py '
              '-p "%s" -u %s -w %s > /etc/cron.d/.%s' %
              (PYTHON, python, settings.CRON_USER, sol,
               settings.CRON_NAME))

        local('mv /etc/cron.d/.%s /etc/cron.d/%s' % (settings.CRON_NAME,
                                                     settings.CRON_NAME))


@task
def pre_update(ref):
    """Update code to pick up changes to this file."""
    execute(disable_cron)
    execute(helpers.git_update, SOLITUDE, ref)
    execute(update_info)


@task
def update():
    create_virtualenv()
    update_db()


@task
def deploy():
    package_dirs = ['solitude', 'venv']
    if os.path.isdir(os.path.join(ROOT, 'aeskeys')):
        package_dirs.append('aeskeys')

    r = helpers.deploy(name='solitude',
                       env=settings.ENV,
                       cluster=settings.CLUSTER,
                       domain=settings.DOMAIN,
                       root=ROOT,
                       package_dirs=package_dirs)

    helpers.restart_uwsgi(getattr(settings, 'UWSGI', []))

    execute(install_cron, r.install_to)
    with lcd(SOLITUDE):
        local('%s manage.py statsd_ping --key=update' % PYTHON)
