# This is designed to be run from fig as part of a
# Marketplace development environment.

# NOTE: this is not provided for production usage.
FROM mozillamarketplace/centos-mysql-mkt:0.2

RUN yum install -y supervisor

ENV IS_DOCKER 1

RUN mkdir -p /pip/{cache,build}
ADD requirements /pip/requirements
WORKDIR /pip
RUN pip install -b /pip/build --download-cache /pip/cache --no-deps -r /pip/requirements/dev.txt --find-links https://pyrepo.addons.mozilla.org/

# Technically this should be in supervisor.conf, if the value is placed there,
# when you enter a bash prompt on the container this value is unset. Meaning
# that tests, dbshell and other really useful commands fail.
#
# To compensate supervisor.conf sets this environment variable to a blank
# string, proving that the solitude proxy can run without this value set.
ENV SOLITUDE_DATABASE mysql://root:@mysql:3306/solitude
EXPOSE 2602
