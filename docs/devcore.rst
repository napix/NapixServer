=========================
Core development on Napix
=========================

You want to develop on Napix?

Installation
============

git clone
---------

Napix is hosted on a Git repository at
``ssh://git@gitlab.enix.org/napix/napixserver.git``.

Config
------

Napix requires a virtual env.
If you don't want a virtualenv, you're on your own.

You may set the virtualenv wherever you like.
**Do not** install the :mod:`napixd` package in the virtualenv.
The ``HOME`` of your Napix Server will be in the root of the Git repo.


Running
-------

In order to run server, run the :program:`napixd` in the :file:`bin`
directory of the repo.
The path of the repo is added to the :envvar:`PYTHONPATH`.

Writing code
============

Rules
-----

Use **4 spaces**.

.. image:: images/tabsspacesboth.png

The PEP-8 should be respected.
However, the maximum width of the lines is increased to 100 characters.


Versions
--------

The Python code is expected to run on Python 2.6 and Python 2.7.
There should **not** be hacks for the support of older versions.

Hacks may be added for the support of different runtimes (PyPy, Jython, etc)
or for the version of Python > 3.


Dependencies
------------

Napix Server **does not requires any dependency** to operate at a basic level.
All the features requiring a dependency are optional.
Optional features may be started by default,
for example the :mod:`Dotconf loader<napixd.conf.dotconf>` is enabled by default
but the :mod:`dotconf` is not a required dependency.

If a dependency is required to run the Server, it must be added to the
``install_requires`` of the :file:`setup.py`.
If the dependency is required by a default feature of the Napix server,
it should be added in the :file:`requirements.txt`.

Tests
=====

Napix includes an extensive test suite.

Running the tests
-----------------

The Napix Server test suite uses :mod:`nose` for the discovery
and the execution of the tests.

In the root directory of the repo, running :program:`nosetests`
runs all the available tests.
The available tests are all those that have their dependencies satisfied.


Dependencies
************

The test suite of Napix requires a few dependencies.

The dependencies are listed in :file:`tests/requirements.txt`
Napix uses :mod:`mock` and :mod:`unitest2`.

The :mod:`unittest2` is *historically* used but :mod:`unittest`
should be preferred.

Writing a test
--------------

When you add a feature or identify a bug you should add a test.

Each Python source file has a test in the :file:`tests` directory.
The name of the test file is the same as the Python source with
the file and directory names prefixed by ``test_``,
so that the discovery detects only the tests.
For example, tests of classes defined :file:`napixd/loader/importers.py`
are written in :file:`tests/test_loader/test_importers.py`.


Dependency of the tests
-----------------------

Dependencies of the test module
*******************************

If the test file requires a library or a framework to import,
the dependency should be added to :file:`tests/requirements.txt`

The tests suite already uses the standard library :mod:`unittest`.
The addition of new dependencies should serve a real interest
for the whole Napix Server tests suite and not only one module.

Dependencies of the code
************************

If the tested code requires a dependency out of the standard library of Python
(or for a specific version of Python), the tests file must be imported
without causing a :exc:`ImportError`.

The ``import`` clause of the *dependency* should be wrapped with a ``try``,
and in case of an :exc:`ImportError`, a :obj:`__test__` value is set to ``False``,
the actual import of the desired module is done in the ``else`` clause.

.. code-block:: python

    try:
        import dotconf
    except ImportError:
        __test__ = False
    else:
        from napixd.conf.dotconf import ConfFactory

The :obj:`__test__` value is detected by :mod:`nose` and skips all the tests
defined in the file.

.. note::

    When the import of the tested feature is done in the ``try`` section,
    misnamed imports are not raised.

The rest of the class definitions of the remaining of the file should happen
with or without the dependency.

Using Tox
---------

A Tox configuration is ready in the Napix Server repo.

