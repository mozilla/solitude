# This is designed to be run from fig as part of a
# Marketplace development environment.

# NOTE: this is not provided for production usage.
FROM mozillamarketplace/centos-mysql-mkt:latest

RUN yum install -y supervisor bash-completion cronie && yum clean all

ENV IS_DOCKER 1

# Copy requirements over first to cache the build.
COPY requirements /srv/solitude/requirements

# Download this securely from pyprepo first.
RUN pip install --no-deps --find-links https://pyrepo.stage.mozaws.net/ peep
RUN peep install \
    --no-deps \
    -r /srv/solitude/requirements/dev.txt \
    -r /srv/solitude/requirements/compiled.txt \
    --find-links https://pyrepo.stage.mozaws.net/

# Ship the source in the container, its up to docker-compose to override it
# if it wants to.
COPY . /srv/solitude
RUN cd /srv/solitude && git show -s --pretty="format:%h" > git-rev.txt

# Technically this should be in supervisor.conf, if the value is placed there,
# when you enter a bash prompt on the container this value is unset. Meaning
# that tests, dbshell and other really useful commands fail.
#
# To compensate supervisor.conf sets this environment variable to a blank
# string, proving that the solitude proxy can run without this value set.
ENV SOLITUDE_DATABASE mysql://root:@mysql:3306/solitude
EXPOSE 2602

# Preserve bash history across image updates.
# This works best when you link your local source code
# as a volume.
ENV HISTFILE /srv/solitude/docker/bash_history
# Configure bash history.
ENV HISTSIZE 50000
ENV HISTIGNORE ls:exit:"cd .."
# This prevents dupes but only in memory for the current session.
ENV HISTCONTROL erasedups

# Add in the cron jobs.
RUN mkdir -p /var/log/solitude/transactions/
RUN python /srv/solitude/bin/crontab/gen-crons.py -w /srv/solitude -p python --dir /var/log | crontab -
