
========================
Install and deploy Napix
========================

Installation
============

The Napix daemon is hosted in a Git repo at git@gitlab.enix.org:napix/napixserver.git
Builds are also available on http://builds.enix.org/napix/.
If you intend to work on napixd, clone the repo.
Else use the built version.
Either way, you should use a virtual env

From the repo::

    git clone git@gitlab.enix.org:napix/napixserver.git
    cd napixserver
    virtualenv venv
    source venv/bin/activate
    pip install requirements.txt
    python setup.py develop

From the package::

    virtualenv napix
    source napix/bin/activate
    pip install http://builds.enix.org/napix/napixd-latest.tar.gz


Dependencies
------------

The napix daemon needs

python
    Versions 2.6 and 2.7 are supported
bottle > 0.10
    Lightweight web framework
gevent (optional)
    Green threads and event loop library
redis-python (optional)
    Redis client (for the shared store)
unittest2 (optional)
    Test framework (for the unit tests)
pyinotify (optional)
    Detection of file modification (automatic reloading of modified source files)


The HOME
--------

Napix finds its configuration, its managers and save its logs and stored files in its ``HOME.``
Napixd ty to guess where is its home.
It looks in the parent directory of the code and in ``~/.napixd/``.

Napix use the repo as its HOME, if you cloned the repo and in ``~/.napixd/`` if you installed the package.
The ``HOME`` can be forced with the :envvar:`$NAPIXHOME`.
Napix creates its ``HOME`` and a bunch of directories inside: ``conf``, ``logs`` and ``auto``.

