=====================
Set up a Napix Server
=====================

.. _installation:

Installation
============

Install the napix server::

    virtualenv napix
    source napix/bin/activate
    pip install -i http://pi.enix.org http://builds.enix.org/napix/napixd-latest.tar.gz

.. note::

   If you already have gevent installed from debian package, you can tell to virtual-env to use it ::
       # virtualenv --system-site-package venv

   If you want to get it directly from git (after activating the virtualenv)::
       (napix)$ pip install cython -e git://github.com/surfly/gevent.git@1.0rc2#egg=gevent


Run the napix server a first time so it initializes its internal structure::

    (napix)$ napixd only
    Napixd Home is /home/user/.napixd
    INFO:Napix.console:Napixd Home is /home/user/.napixd
    Options are only
    INFO:Napix.console:Options are only
    Starting process 25367
    INFO:Napix.console:Starting process 25367
    Logging activity in /home/user/.napixd/log/napix.log
    INFO:Napix.console:Logging activity in /home/user/.napixd/log/napix.log
    INFO:Napix.conf:Using /home/user/.napixd/conf/settings.json configuration file
    INFO:Napix.Server:Starting
    Stopping
    INFO:Napix.console:Stopping
    Stopped
    INFO:Napix.console:Stopped

The second line *Napixd Home is* **path** tells what the HOME of Napix is.
Napix finds its configuration, its managers and save its logs and stored files in its HOME.

The HOME can be forced with ``NAPIXHOME`` environment variable.

The :program:`napixd` program takes arguments.
The arguments are options to enable or disable features, processed sequencially.
The ``only`` option disable everything. You can find a list of options by running ``napixd help``.

The development setup
=====================

In order to develop on napix without being embarrassed with extra features::

    napixd only print_exc times gevent app reload useragent webclient auto

This setup disable authentication and notifications and print the caught exceptions in the console.

You can add Napix Managers in ``HOME/auto``

.. _helloworld:

Install a module
================

Modules come from two sources: the config file and the ``auto`` directory.
In the config file, modules are listed in the mapping ``Napix.managers``.

Edit ``HOME/conf/settings.json`` and add  the follwing inside the braces after ``managers``::

    managers {
        bonjour = 'napixd.contrib.helloworld.ConfiguredHelloWorld'
    }


Stop the server by pressing ``Ctrl-C`` and restart it.
Open a browser at http://127.0.0.1:8002/hello/ and http://127.0.0.1:8002/hello/world .
You can see the `hello world` module in action.

See :ref:`first_step` to learn how to write your own modules.

.. _configuration:

Configure a module
==================

Module added by the config file may receive a configuration.
The configuration is stored in the root object of the configuration.

Edit ``HOME/conf/settings.conf`` and add the following inside the braces after
``managers`` inside ``Napix`` ::

    managers {
        bonjour = 'napixd.contrib.helloworld.ConfiguredHelloWorld'
        gutentag = 'napixd.contrib.helloworld.ConfiguredHelloWorld'
    }

ConfiguredHelloWorld does the same as HelloWorld, but it takes a configuration.
The configuration of ConfiguredHelloWorld contains a key **hello** that links to a localized hello world message.

Add the configuration inside the conf file, outside of ``Napix``::

    Manager 'bonjour' {
        hello = 'Le monde'
    }
    Manager 'gutentag' {
        hello = 'Die Welt'
    }

Restart the Napix Server and open your browser at http://127.0.0.1:8002/bonjour/world and http://127.0.0.1:8002/gutentag/world .
You can see ``{ "hello" : "Le monde" }`` and ``{ "hello" : "Die Welt" }``
