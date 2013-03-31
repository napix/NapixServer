===============================
The napix configuration System
===============================

Napix uses a configuration file stored in :file:`HOME/conf/settings.json`.
The configuration is stored as a JSON object.

Loading
=======

Default Configuration
---------------------

A default configuration sample is written if no configuration file is found.
This configuration file is empty, but contains the structure of the expected configuration::

    (nx)root@debian:~# napixd
    Napixd Home is /root/.napixd
    INFO:Napix.console:Napixd Home is /root/.napixd
    ...
    WARNING:Napix.conf:Did not find any configuration, trying default conf
    INFO:Napix.conf:Try to write default conf to /root/.napixd/conf/settings.json
    INFO:Napix.conf:Conf written to /root/.napixd/conf/settings.json
    ...

Bad JSON file
-------------

If the parsing of the JSON file causes an error,
the launch of the server is stopped and a CRITICAL error is printed on the terminal::

    CRITICAL:Napix.Server:Configuration file HOME/conf/settings.json contains a bad JSON object (Extra data: line 2 column 11 - line 41 column 1 (char 11 - 1393))

Comments
========

Some JSON parser allow the use of javascript's comments with ``//`` and ``/* ... */``.
The JSON RFC does not allow any text outside of the strings.
The Python JSON parser follows the RFC.

By convention, comments in the Napix JSON file are keys starting with a ``#``.
:class:`napixd.conf.Conf` ignores all keys starting by a ``#``.
Comments on a key should be this key with a ``#`` at the beginning and placed before the commented key.
The comment on a object should be a key ``#info`` just after the openning ``{``::

    {
      "Napix" : {
        "#info" : [
            "The default configuration for a Napix server.",
            "Directives starting by a # are comments."
        ],
        "#description" : "A human description of the purpose of this napix",
        "description" : "The base Napix server"
    }

.. warning:: Difference between writing Python and JSON

   - JSON files are always encoded in UTF-8.
   - ``'`` are not string delimiters, only ``"``.
   - Trailing ``,`` are forbidden.



Structure
=========

The Napix key
-------------

All the configuration used internally by Napix is stored in the ``Napix`` key.

Napix.description
.................

A human description of this Napix instance.

.. _conf.napix.managers:

Napix.managers
..............

A mapping of alias to a fully qualified class name::

    "managers" : {
        "hello" : "napixd.contrib.helloworld.HelloWorld"
    }

.. _conf.napix.auth:

Napix.auth
..........

auth_url
    The authentication URL. (A NapixCentral server)
service
    The name of this service in the permissions

.. _conf.napix.notify:

Napix.notify
............

The notifier section

credentials
    A mapping of **login** an **key** used by the notification background task to contact the Napix Directory
delay
    The time between notifications
url
    The address of the Napix Directory

.. _conf.napix.storage:

Napix.storage
.............

The configuration of stores.

store
    The default backend for Key-Value storage
counter
    The default backend for counters


The other keys
--------------

Every other key stored in the root of the configuration object are used for the managers.

The key of the mapping is the alias of the module
and the value is the fully qualified name to the class.
