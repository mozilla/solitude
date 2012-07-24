========================================
Solitude
========================================


Solitude is a payments server for processing payments for Mozilla's Marketplace
and Addons site.

It provides a REST API for processing payments that you would plug into your
site. We've implemented the APIs that we want to use for the Marketplace, not
every API that the provider supports.

Currently we support:

* some `PayPal <https://www.paypal.com/>`_ APIs
* some `BlueVia <https://bluevia.com/en/>`_ support

This project is based on **playdoh**. Mozilla's Playdoh is an open source
web application template based on `Django <http://www.djangoproject.com/>`_.

Contents
--------

.. toctree::
   :maxdepth: 2
   :glob:

   topics/*

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
