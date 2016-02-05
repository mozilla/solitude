========================================
Solitude
========================================

*Please note:* this project is currently unmaintained and is not (or soon will not) be in active use by Mozilla.

Solitude is a payments server for processing payments for Mozilla's Marketplace
and Addons site.

.. figure:: _static/solitude.svg
        :align: right
        :target: http://www.breweryvivant.com/

It provides a REST API for processing payments that you would plug into your
site. We've implemented the APIs that we want to use for the Marketplace, not
every API that the provider supports.

Currently we support:

* some `Bango <http://bango.com/>`_ APIs
* some `Braintree <https://www.braintreepayments.com/>`_ APIs
* some `Zippy <http://zippypayments.readthedocs.org/>`_ compliance

In the past PayPal was supported, that has been removed.

This project is based on **playdoh**. Mozilla's Playdoh is an open source
web application template based on `Django <https://www.djangoproject.com/>`_.

This document is available as a `PDF <https://media.readthedocs.org/pdf/solitude/latest/solitude.pdf>`_.

Solitude is also a nice tasting beer from `Brewery Vivant <http://www.breweryvivant.com/>`_. The logo is
theirs.

Contents
--------

.. toctree::
   :maxdepth: 2

   topics/setup.rst
   topics/security.rst
   topics/overall.rst
   topics/auth.rst
   topics/generic.rst
   topics/bango.rst
   topics/braintree.rst
   topics/zippy.rst
   topics/proxy.rst
   topics/services.rst

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
