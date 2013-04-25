========================================
Solitude
========================================


Solitude is a payments server for processing payments for Mozilla's Marketplace
and Addons site.

.. image:: http://breweryvivant.com/images/sized/images/uploads/solitude-logo-lg_1-250x349.png
        :align: right
        :target: http://breweryvivant.com/index.php/the-beer/packaged-beer/solitude/

It provides a REST API for processing payments that you would plug into your
site. We've implemented the APIs that we want to use for the Marketplace, not
every API that the provider supports.

Currently we support:

* some `PayPal <https://www.paypal.com/>`_ APIs
* some `Bango <http://bango.com/>`_ support

This project is based on **playdoh**. Mozilla's Playdoh is an open source
web application template based on `Django <http://www.djangoproject.com/>`_.

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
   topics/paypal.rst
   topics/async.rst

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
