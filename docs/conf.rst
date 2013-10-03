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

All the modules in the alias are loaded at the start of the Napix Server.
If a module fails to import or load, the Napix server does not start.

The path may be used multiple times with different aliases.
Napix will run multiple instance of the same manager, on different paths.

.. _conf.napix.auth:

Napix.auth
..........

auth_url
    The authentication URL. (A NapixCentral server)
service
    The name of this service in the permissions
get_parameter
    The GET parameter used by non-secure authentication

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


Configuration of the managers
=============================

When the :class:`napixd.services.Service` instantiates a manager,
it calls its :meth:`napixd.managers.base.Manager.configure` method with the configuration.
The method is called with a :class:`napixd.conf.Conf` instance.

Multiple services with the same Manager class can run with different configurations.


Configuration of the submanagers
--------------------------------

The configuration of each sub-manager of a manager is found in its parent's configuration.
The key is the name of the sub-manager.

Example
.......

.. code-block:: python

    class VHostManager( Manager):
        managed_class = [ 'PasswordManagers' ]
        name = 'vhost'
        def configure( self, conf):
            self.conf_dir = conf.get('conf_dir', '/etc/httpd' )
            self.var_dir = conf.get('var_dir', '/var/www')
    class PasswordManagers( Manager):
        name = 'passwords'
        def configure( self, conf):
            self.min_pass_size = conf.get('min_pass_size', 8)

.. code-block:: javascript

   {
        "conf_dir" : "/etc/apache.d",
        "passwords" : {
            "min_pass_size" : 5
        }
   }

PasswordManagers is configured with **min_pass_size** = 5.


Source of the configuration
---------------------------

The configuration source of a manager depends on its :class:`loader<napixd.loader.importers.Importer>`.

The :class:`auto-loader<napixd.loader.importers.AutoImporter>` which is used with the files found in the `auto` folder,
tries to parse JSON from the docstring of the configure method **of the root manager**.

.. code-block:: python

    class VHostManager( Manager):
       managed_class = [ 'PasswordManagers' ]
       name = 'vhost'
       def configure( self, conf):
           """{
            "conf_dir" : "/etc/apache.d",
            "passwords" : {
                "min_pass_size" : 5
            }
           }
           """
           self.conf_dir = conf.get('conf_dir', '/etc/httpd' )
           self.var_dir = conf.get('var_dir', '/var/www')
    class PasswordManagers( Manager):
        name = 'passwords'
        def configure( self, conf):
            self.min_pass_size = conf.get('min_pass_size', 8)

The load from the :class:`configuration<napixd.loader.importers.ConfImporter>` used with :ref:`conf.napix.managers`
get the configuration from the same configuration file.
The key is the same as the alias of the managers in the ``Napix.managers`` map.

.. code-block:: javascript
   :emphasize-lines: 4,7

   {
        "Napix": {
            "managers" : {
                "password" : "my.path.to.VHostManager"
            }
        },
       "password" : {
        "conf_dir" : "/etc/apache.d",
        "passwords" : {
            "min_pass_size" : 5
        }
   }
