.. _options:

======================================
Launching and running the Napix Server
======================================

Launching the service
=====================

Standard interface
------------------

There is two ways to start the Napix server: use the :program:`napixd` runnable
or use the wsgi interface.

The wsgi :data:`~napixd.wsgi.application` follows the Python conventions and is located in the module :mod:`napixd.wsgi`.
The runnable :program:`napixd` will launch this application with the selected wsgi server (see `gevent` and `rocklet` options)

Application interface
---------------------

Napix uses a class to prepare and launch its server.
In order to customize the launch sequence or to integrate Napix in another application,
the class :class:`napixd.launcher.Setup` and the helper function :func:`napixd.launcher.launch` are available.

Options
=======

At the start of the daemon, Napix looks in its arguments (:data:`sys.argv`)
to find which options it must launch.

An option is enabled if its name is the arguments or if its enabled by default.
The options defines which optional features will run or not.

.. note::

   The options names are not checked.
   A misspelled option name will be accepted by :program:`napixd` without any warning.

An option can be disabled by using prefixing the name with ``no``::

    $ napixd options
    Enabled options are: auto app auth reload gevent conf cors useragent options webclient

    $ napixd options noapp uwgsi
    Enabled options are: auto auth reload gevent uwgsi conf cors useragent noapp options webclient


Special options
---------------

The special options do not enable special features.
They are intended for debugging and documentation.

:help:
    Show the help message and the available options and quit.

:only:
    Disable the default options.

:option:
    Show the enabled options and quit.

Default options
---------------

:app:
    Launch the :data:`~napixd.wsgi.application`

:useragent:
    Show a human readable page for the users requesting an url directly from the browser.
    See :class:`napixd.plugins.conversation.UserAgentDetector`.

:auth:
    Enable the :ref:`auth`
:central:
    Use a Napix Central Server

:reload:
    Enable the :ref:`reloading`

:webclient:
    The web interface accessible on ``/_napix_js/``

:gevent:
    Use :mod:`gevent` as the wsgi interface.
    When gevent is disabled, the :mod:`wsgiref` of the standard library of Python is used.

:auto:
    Automatically detect and :class:`loads<napixd.loader.importers.AutoImporter>` from :file:`HOME/auto/` directory.
    See :ref:`auto-loading`

:conf:
    :class:`Load<napixd.loader.importers.ConfImporter>` from the :ref:`conf.managers` section of the config

:time:
    Add custom header to show the duration of the request.
    See :mod:`napixd.plugins.times`.

:logger:
    Standardize the ouptut on the console accross servers
    See :class:`napxid.plugins.middleware.LoggerMiddleware`.

:docs:
    Generate automated documentation
    See :mod:`napixd.docs`

:dotconf:
    Use a dotconf file as the source of configuration


Non-default
-----------
:notify:
    Enable the :ref:`notify`

:uwsgi:
    Use with uwsgi.

:silent:
    Do not show the messages in the console

:verbose:
    Augment the ouptut of the loggers

:print_exc:
    Show the exceptions in the console output

:times:
    Add custom header to show the total time and the time spent without the IO.
    It requires :mod:`gevent`.

:pprint:
    Enable pretty printing of the JSON output

:cors:
    Add Cross-Site Request Service headers

:secure:
    Use only signed authentication and not deny requests signed by a GET token.
    See :ref:`non-secure-auth`.

:autonomous-auth:
    Use :ref:`autonomous-auth` in the authentication process.

:localhost:
    Listen on the loopback interface only

:hosts:
    Check the HTTP Host header
    See :ref:`conf.hosts`

:jwt:
    Enable the :mod:`JSON Web Token Source<napixd.auth.jwt>`
