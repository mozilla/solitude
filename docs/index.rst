========================================
Solitude
========================================


Solitude is a payments server for processing payments for Mozilla's Marketplace
and Addons site.

.. figure:: _static/solitude.svg
        :align: right
        :target: http://www.breweryvivant.com/#!packaged-beer/cais

It provides a REST API for processing payments that you would plug into your
site. We've implemented the APIs that we want to use for the Marketplace, not
every API that the provider supports.

Currently we support:

* some `PayPal <https://www.paypal.com/>`_ APIs
* some `Bango <http://bango.com/>`_ APIs
* some `Boku <http://www.boku.com/>`_ APIs
* some `Zippy <http://zippypayments.readthedocs.org/>`_ compliance

This project is based on **playdoh**. Mozilla's Playdoh is an open source
web application template based on `Django <http://www.djangoproject.com/>`_.

This document is available as a `PDF <https://media.readthedocs.org/pdf/solitude/latest/solitude.pdf>`_.

Solitude is also a nice tasting beer from `Brewery Vivant <http://breweryvivant.com/>`_. The logo is
theirs.

Contents
--------

.. toctree::
   :maxdepth: 2

   topics/setup.rst
   topics/security.rst
   topics/auth.rst
   topics/generic.rst
   topics/bango.rst
   topics/boku.rst
   topics/paypal.rst
   topics/zippy.rst
   topics/proxy.rst
   topics/services.rst

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
