
========================
Install and deploy Napix
========================

Installation
============

The Napix daemon is hosted in a Mercurial repo at ssh://hg@the-book.enix.org/NapixServer.
Builds are also available on http://builds.enix.org/napix/.
If you intend to work on napixd, clone the repo.
Else use the built version.
Either way, You should use a virtual env

From the repo::

    hg clone ssh://hg@the-book.enix.org/NapixServer
    cd NapixServer
    virtualenv venv
    source venv/bin/activate
    pip install requirements.txt
    python setup.py develop

From the package::

    virtualenv napix
    source napix/bin/activate
    pip install git+git://github.com/SiteSupport/gevent.git
    pip install http://builds.enix.org/napix/napixd-latest.tar.gz

.. note::

   If it failed in the gevent build step, install python-dev and cython::

       # apt-get install python-dev
       (venv)$ pip install cython


Dependencies
------------

The napix daemon needs

python
    Versions 2.6 and 2.7 are supported
bottle > 0.10
    Lightweight web framework
gevent
    Green threads and event loop library
redis-python (optional)
    Redis client (for the shared store)
unittest2 (optional)
    Test framework (for the unit tests)
pyinotify (optional)
    Detection of file modification (automatic reloading of modified source files)


Configuration
=============

The HOME
--------

Napix finds its configuration, its managers and save its logs and stored files in its ``HOME.``
Napixd ty to guess where is its home.
It looks in the parent directory of the code and in ``~/.napixd/``.

Napix use the repo as its HOME, if you cloned the repo and in ``~/.napixd/`` if you installed the package.
The ``HOME`` can be forced with the :envvar:`$NAPIXHOME`.
Napix creates its ``HOME`` and a bunch of directories inside: ``conf``, ``logs`` and ``auto``.

Configuration
-------------

Napix takes its configuration in the conf/settings.json.

.. literalinclude:: /samples/settings.json
    :language: javascript


Napix.auth
..........

The ``Napix.auth`` key sets the value of the authentication server.

The value ``service`` is the **public address** at which the Napix server is accessed.
The client will sign its request with this public address.
The Napix server will check that it is the host at which the request is addressed by comparing its host value and the request host.

The ``auth_url`` value will set the address at which the server will ask for the confirmation of the requests authenticity.

.. note::

   If you don't want to bother with the authentication, use ``noauth`` option::

       $ napixd noauth


Modules Loading
===============

Loading by the configuration
----------------------------

The configuration object ``Napix.managers`` is a hashmap
where the keys are an alias and the value is the dotted python path to a Manager.
Multiple instance of a single manager class can be loaded, with different aliases.
The detect (cf :ref:`Auto-loading<auto-loading>`) classmethod is not called.

In order to specify the configuration for an instance of a Manager,
you can add a value in the root object of the configuration.

In this example, two X480 are managed by this Napix server, they use the same manager, and different IP and credentials.

.. literalinclude:: /samples/conf.json
    :language: javascript

.. _auto-loading:

Auto-loading
------------

If there is a file ending by **.py** in a auto-detect folder
of the Napix setup (:file:`/var/lib/napix/auto` or :file:`NapixServer/auto`),
the Napix loader will import this python file and add all the subclasses of :class:`managers.Manager` in the available managers.
The auto loaded managers may override the classmethod :meth:`~managers.Manager.detect`
which tells if the managers should be loaded.
By default detect return True when the class is not a base method defined inside Napix.

This feature does not allow neither multiple loading of the same manager nor the configuration.

Reloading
---------

Napix proposes an option to reload the modules without stopping the server.
When the reload is triggered, the configuration is reparsed.
The autoload directories are scanned again.

The automatic reloading is disabled when ``Napix.loader.reload`` is set to false.

GET /_napix_reload
..................

When the server is on DEBUG mode, a simple GET on /_napix_reload will trigger a reload.
It is useful for a developer, he just refreshes /_napix_reload then refreshes his page.

Send a SIGHUP signal
....................

Sending a SIGHUP to the server will cause it to reload::

    $ ps aux  | grep napixd
    napixd     13651  0.5  2.4  81000 12560 pts/3    Sl+  05:24   0:17 python bin/napixd
    $ kill -HUP 13651

Use inotify
...........

When inotify is available through ``pyinotify``,
it will listen on the filesystem changes to check if the auto-loaded directories changed,
and it will then issue a reload.

