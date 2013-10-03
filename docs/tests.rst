=================
Automated Testing
=================

Napix Server is thoroughly tested by unit tests.


Running the tests
=================

All the tests of the napix servers are contained in the :file:`tests` directory.
The dependencies are defined in the :file:`test/requirements.txt`::

    (venv)$ pip install -r tests/requirements.txt

The tests use :program:`nosetests` of the module :mod:`nose` to run::

    (venv)$ pip install -r nose
    (venv)$ nosetests


Computing the coverage
----------------------

The code coverage statistics require the :mod:`coverage` package.

:mod:`nose` handle the coverage computations::

    (venv)$ nosetests --with-coverage --cover-package=napixd


Writing tests
=============

If you want to write a test to isolate a bug or a regression, or for a new
feature, you have to write or edit a test module in the :file:`tests` directory.

A test file should contain tests only for a single module.
The test module is named like the module with the prefix **test_**.
Packages have a **test_** directory with the package name containing the
tests of the modules inside the package.

The tests use :mod:`unittest` or :mod:`unittest2`.
The former is recommended unless features available in the second are required.

.. note::

    The way :mod:`nose` works requires that all test package, modules, classes,
    methods, etc, contains *test*.

