=============
Simple Usage
=============

Installation
============

Using pip
---------

The napixd service is easily installable by using pip.
A virtual environment is recommended.
Installation process using a Virtual-env::

    virtualenv napix
    cd napix
    source bin/activate
    pip install http://builds.napix.io/latest/napixd dotconf

.. _usage-gevent:

gevent
------

The napixd daemon uses the gevent event loop in order to handle concurrency.
Gevent is recommended for the services using long treatments, or heavy loads.

Napixd requires a version 1.0 of gevent.

gevent requires cython to compile and is installable from the git repo::

    (napix)$ pip install gevent

nogevent
^^^^^^^^

The server does not requires gevent.
It is a default option, but it's easily disabled by using the nogevent option::

    (napixd)$ napixd nogevent


--system-site-package
^^^^^^^^^^^^^^^^^^^^^

if you already have gevent installed from debian package,
you can tell to virtual-env to use it::

    $ virtualenv --system-site-package venv


configuration
=============

Authentication settings
-----------------------

The napixd server comes *batteries included* with an authentication protocol.

central
^^^^^^^

A Napix server delegates the check of authentication and authorisation
to a third-party host running a Napix Central server.

The configuration of the central requires an *url* in the section *auth*::

    #conf/settings.json
    auth {
        url = 'http://auth.napix.io:8003/auth/authorization/'
    }

autonomous-auth
^^^^^^^^^^^^^^^

The server napixd can run with an autonomous authentication layer,
meaning that no third-party server is required.

The authentication is made with a local password,
through the same protocol as the authentication from the server.
This is totally transparent for the client.

The password is set by the key *password* of the section *auth*::

    #conf/settings.conf
    auth {
        password = 'secret'
    }

.. warning::

   Save the config file with the UTF-8 encoding.


See :ref:`autonomous-auth`.

noauth
^^^^^^^

The option ``noauth`` disable the authentication protocol entirely.
This option overrides ``autonomous-auth``.

Modules
-------

Each value of the *managers* section refers to a manager instanciated into the server.
The key is the **alias** of the manager.
The url of the objects managed by this manager will all be contained into this alias::

    #conf/settings.conf
    managers {
        local = 'napixd.contrib.host.HostInfo'
    }

Multiple instances of the same manager are possible with differents aliases.

Configuration of modules
^^^^^^^^^^^^^^^^^^^^^^^^

Add a *Manager* section in the configuration file with the alias of the manager::

    managers {
        local = 'napixd.contrib.host.HostInfo'
    }
    Manager 'local' {
        key = 'value'
    }

Storage configuration
---------------------

Production
==========

uwsgi
-----

When launched with :program:`uwsgi`, the napxid server must be started with the ``uwsgi`` :ref:`option<options>`::

    uwsgi --pyargv uwsgi --wsgi napixd.wsgi --http localhost:8002

.. warning::

   The ``localhost`` option and the :option:`--port` are not considered when using uwsgi.

Backups
-------
