.. highlight:: python

.. currentmodule:: napixd.managers

.. _first_step:

=======================================
First steps in the writing of a manager
=======================================

In Napix, managers behaves like collection and have the logic to maintain a set of resources.

Napix uses the REST approach: an URI defines a resource and HTTP verbs ( GET, PUT, POST, etc) defines the action on it.
PUT /htaccess/toto is used to modify the resource identified by /htaccess/toto with the data given in the request body.
GET /htaccess/toto is used to retrieve the same resource.
GET /htaccess/tata retrieves another resource.

Napix uses :class:`~base.Manager` subclasses to handle the collections logic.
Each Manager instance represents a collection and provides methods to manage the collection.

Launch
======

The first step is to launch the server as described in :ref:`installation`.
Install pyinotify to enable the auto-reloading, and the napix client to query the server::

    (napix)$ pip install pyinotify
    (napix)$ pip install http://builds.enix.org/napix/NapixCLI-latest.tar.gz

When launching the napixd daemon, it shows its PID (Starting process xx),
its root directory (Found napixd home at /xxx),
the log file ( Logging activity in /xxx),
the socket on which it is listening ( Listening on http://xxx:xxx/).

The server can be stopped by hitting Ctrl+c::

    (napix)$ bin/napixd nodoc debug print_exc noauth nonotify
    Napixd Home is /home/napix/NapixServer/new_home
    INFO:Napix.console:Napixd Home is /home/napix/NapixServer/new_home
    Options are print_exc,auto,app,nodoc,reload,gevent,noauth,nonotify,cors,debug,useragent,webclient
    INFO:Napix.console:Options are print_exc,auto,app,nodoc,reload,gevent,noauth,nonotify,cors,debug,useragent,webclient
    Starting process 12528
    INFO:Napix.console:Starting process 12528
    Logging activity in /home/napix/NapixServer/new_home/log/napix.log
    INFO:Napix.console:Logging activity in /home/napix/NapixServer/new_home/log/napix.log
    INFO:Napix.conf:Using /home/napix/NapixServer/new_home/conf/settings.json configuration file
    INFO:Napix.reload:Launch Napix autoreloader
    INFO:Napix.Server:Using /home/napix/NapixServer/napixd/web as webclient
    INFO:Napix.Server:Starting
    Bottle v0.11.6 server starting up (using GeventServer())...
    Listening on http://0.0.0.0:8002/
    Hit Ctrl-C to quit.

.. note::

   In this example ``HOME`` is ``/home/napix/NapixServer/``.
   Yours may be different.
   You can force your ``HOME`` with the environment variable :envvar:`$NAPIXHOME`.
   For example set it inside your venv. Run ``napixd`` to create the structure inside::

       (napix)$ export NAPIXHOME=$VIRTUAL_ENV
       (napix)$ napixd only

You can check that the server is up and responding by poking it with napix::

    napix -s localhost:8002
    >> ls
    [ ]

.. note::

   if you have installed HelloWorld in :ref:`helloworld`, ``ls`` will show ``hello``

Write a manager
===============

.. note::

   The examples below use differents snippet from different sessions.

    Without a prompt, is python source code inside the :file:`HOME/auto/password.py`.

    A ``(napix)$`` indicates a shell with the virtualenv loaded::

            (napix)$ napixd noauth

    A ``>>`` indicates an interactive session within the napix client::

        (napix)$ napix -s localhost:8002
        >> get /

    A ``>>>`` indicates an interactive python shell

        (napix)$ python
        >>> import os


The auto-loader directory is the auto-folder inside the root directory.
Here it is /home/user/NapixServer/auto.

Launch your favorite editor with and open a file in the auto-load directory :file:`~/.napixd/auto/password.py`.
Write the headers and save.

.. literalinclude:: /samples/basicpasswordfile.py
    :lines: 1-2

.. warning::

   :file:`~/.napixd/` is your default HOME. Change the path if you changed the HOME.

The autoloader will detect the filesystem operation and launch a reload.
A line ``Reloading`` will appear in the log of the napixd daemon console.::

    (napix)$ bin/napixd
    Starting process 1482
    Found napixd home at /home/user/NapixServer
    Logging activity in /tmp/napix.log
    Bottle server starting up (using RocketAndExecutor())...
    Listening on http://0.0.0.0:8002/
    Hit Ctrl-C to quit.

    Reloading

A curl request will still show an empty array, because there isn't a Manager yet to be loaded::

    >> get /
    [ ]

Continue writing in the previously opened file.

.. literalinclude:: /samples/basicpasswordfile.py
    :lines: 6

The :class:`default.DictManager` class is a subclass of :class:`~base.Manager`
which simplifies the way of writing a Manager.
Instead of writing a method to make a modification, retrieve a resource, create it, etc,
the :class:`~default.DictManager` instance store an internal dict of all its resource indexed by id.
The :class:`~default.DictManager` implements the method to modify, create, list, etc and does the operation on the internal dict.

Append the following lines in the password.py file.

.. literalinclude:: /samples/basicpasswordfile.py
    :lines: 12-15

When you save the file, the daemon will reload the managers and find the one you created.
A GET request will show you it.::

    >> get /
    [
        /basicpasswordfile
    ]

If you make a mistake while writing a manager, and it causes the import to fail, Napix will forgive you.
Just correct the error and save.
If an import fails, and makes a manager unavailable, a placeholder will catch the calls and
return the error that cause the import to fail.

For example: add a syntax error or a undeclared name in the file.

.. code-block:: python

    class BasicPasswordFileManager(DictOopsIMadeAMistake):
        """
        Napix server to edit a password file in the user:password format
        """

The requests will fail with an :exc:`ImportError` caused by a :exc:`NameError`::

    >> get /basicpasswordfile/
    Napixd Error ImportError
    /home/napix/NapixServer/napixd/plugins.py in inner_exception_catcher
        120   return callback(*args,**kwargs) #Exception

    /home/napix/NapixServer/napixd/plugins.py in inner_conversation
        60   result = callback(*args,**kwargs) #Conv

    /home/napix/NapixServer/napixd/plugins.py in inner_useragent
        178   return callback( *args, **kwargs)

    /home/napix/NapixServer/napixd/loader.py in inner
        339   raise cause

    ImportError: NameError("name 'DictOopsIMadeAMistake' is not defined",)

Rollback to fix this error before continuing.

An attempt to list the resources (using GET /``name of the manager``/) fails with a :exc:`NotImplementedError`
because the load method that the developer must override is not yet written::


    >> get /basicpasswordfile/
    Napixd Error NotImplementedError
    /home/napix/NapixServer/napixd/plugins.py in inner_exception_catcher
        120   return callback(*args,**kwargs) #Exception

    /home/napix/NapixServer/napixd/plugins.py in inner_conversation
        60   result = callback(*args,**kwargs) #Conv

    /home/napix/NapixServer/napixd/plugins.py in inner_useragent
        178   return callback( *args, **kwargs)

    /home/napix/NapixServer/napixd/services/plugins.py in inner_arguments
        24   return callback(path)

    /home/napix/NapixServer/napixd/services/__init__.py in as_collection
        224   return ServiceCollectionRequest( path, self).handle()

    /home/napix/NapixServer/napixd/services/servicerequest.py in handle
        118   result = self.call(callback,args)

    /home/napix/NapixServer/napixd/services/servicerequest.py in call
        85   return callback(*args)

    /home/napix/NapixServer/napixd/managers/default.py in list_resource
        81   return self.resources.keys()

    /home/napix/NapixServer/napixd/managers/default.py in _get_resources
        67   self._resources = self.load(self.parent)

    /home/napix/NapixServer/napixd/managers/default.py in load
        63   raise NotImplementedError, 'load'

    NotImplementedError: load

You can here observe here the behavior of Napix when an uncaught exception is raised.
It returns a 500 error, with the description of the exceptions serialized in JSON.

The developer still have to write the metadatas of the manager (its documentation and the fields of the resources it manages),
the methods to load and persist the internal dict and a method to tell what is the id of a newly created resource.

The metadata
------------

The metadatas of the Manager are composed of the docstring of the module
which should describe what kind of resources it manages, and the :attr:`~base.Manager.resource_fields` attribute
which documents the names of the attributes of the managed resources and metadatas about them.

The metadatas of the managers have two main goals.
They take part in the auto-documentation of the manager and for the filtering of the input and output.
The resources that are sent to the user are stripped of the fields that are not in the `resource_fields`
and the resource_dict given to the creation and modification method contains only fields in resource_fields.

.. literalinclude:: /samples/basicpasswordfile.py
    :lines: 16,21-30

The resources of our manager will contain a ``username`` and the corresponding ``password``.
The template object proposed to the users will be ``john:toto42``.

This template object is retrieved at ``/basicpasswordfile/_napix_new``::

    >> get /basicpasswordfile/_napix_new
    {
        password: toto42
        username: john
    }

The url namespace is basicpasswordfilemanager.
It is the default value of the lower case class name.
It can be changed by overriding the classmethod :meth:`~base.Manager.get_name`.

.. literalinclude:: /samples/basicpasswordfile.py
    :lines: 32-34

The requests show that the old name is gone replaced by the new one.::

    >> get /
    [
        /passwords
    ]
    >> get /basicpasswordfile/_napix_new
    {
        "password": "toto42",
        "username": "john"
    }

The load method have now to be written.

It takes the parent manager that spawned this one.
The parent is :obj:`None` if it is a first level manager when path is ``/manager/``.

The inheritance cases are treated in :ref:`inheritance`.

.. literalinclude:: /samples/basicpasswordfile.py
    :lines: 4,12,16,36-49

It returns a dict of id pointing to resources::

    #The load method expect a parent argument.
    >>> pfm = BasicPasswordFileManager(None)
    >>> pfm.resources
    {
        'john' : {
            'username' : 'john',
            'password' : 'toto42'
        },
        'mwallace' : {
            'username' : 'mwallace',
            'password' : '666'
        }
    }

Now the manager can be listed and consulted::

    $ echo 'sony_rssi:pikachu1' > /tmp/test
    $ echo 'sony_bigboss:password3' >> /tmp/test
    >> get /passwords/
    [
        /passwords/sony_rssi
        /passwords/sony_bigboss"
    ]
    >> get /passwords/sony_rssi
    {
        password: pikachu1
        username: sony_rssi
    }

But an attempt to modify an existing object will fail.::

    >> put /passwords/sony_rssi password=s4fr34$er- username=sony_rssi
    Napixd Error NotImplementedError
    /home/napix/NapixServer/napixd/plugins.py in inner_exception_catcher
        120   return callback(*args,**kwargs) #Exception

    /home/napix/NapixServer/napixd/plugins.py in inner_conversation
        60   result = callback(*args,**kwargs) #Conv

    /home/napix/NapixServer/napixd/plugins.py in inner_useragent
        178   return callback( *args, **kwargs)

    /home/napix/NapixServer/napixd/services/plugins.py in inner_arguments
        24   return callback(path)

    /home/napix/NapixServer/napixd/services/__init__.py in as_resource
        221   return ServiceResourceRequest( path, self).handle()

    /home/napix/NapixServer/napixd/services/servicerequest.py in handle
        120   self.end_request()

    /home/napix/NapixServer/napixd/services/servicerequest.py in end_request
        94   self.manager.end_request( self.request)

    /home/napix/NapixServer/napixd/managers/default.py in end_request
        130   self.save(self.parent,self.resources)

    /home/napix/NapixServer/napixd/managers/default.py in save
        112   raise NotImplementedError, 'save'

    NotImplementedError: save

Another :exc:`NotImplementedError` this time because we need to override the :meth:`~default.DictManager.save`.
Save takes the parent (the same as in load) and the resources of the managers as argument and persists them to the disk.

Like in the load method, we can ignore the parent argument.

.. literalinclude:: /samples/basicpasswordfile.py
    :pyobject: BasicPasswordFileManager.save

Now the result is persisted::

    >> put /passwords/sony_rssi password=s4fr34$er- username=sony_rssi
    $ cat /tmp/test
    sony_bigboss:password3
    sony_rssi:s4fr34$er-
    >> get /passwords/
    [
        /passwords/sony_bigboss
        /passwords/sony_rssi
    ]

For the creation of a resource, a POST request is sent to the collection::

    >> post /passwords/ password=neo username=tanderson
    Napixd Error NotImplementedError
    /home/napix/NapixServer/napixd/plugins.py in inner_exception_catcher
        120   return callback(*args,**kwargs) #Exception

    /home/napix/NapixServer/napixd/plugins.py in inner_conversation
        60   result = callback(*args,**kwargs) #Conv

    /home/napix/NapixServer/napixd/plugins.py in inner_useragent
        178   return callback( *args, **kwargs)

    /home/napix/NapixServer/napixd/services/plugins.py in inner_arguments
        24   return callback(path)

    /home/napix/NapixServer/napixd/services/__init__.py in as_collection
        224   return ServiceCollectionRequest( path, self).handle()

    /home/napix/NapixServer/napixd/services/servicerequest.py in handle
        118   result = self.call(callback,args)

    /home/napix/NapixServer/napixd/services/servicerequest.py in call
        85   return callback(*args)

    /home/napix/NapixServer/napixd/managers/default.py in create_resource
        148   resource_id = self.generate_new_id(resource_dict)

    /home/napix/NapixServer/napixd/managers/default.py in generate_new_id
        119   raise NotImplementedError, 'generate_new_id'

    NotImplementedError: generate_new_id

A new :exc:`NotImplementedError`, this one comes from the :meth:`~default.DictManager.generate_new_id` method.
In order to create a new resource, the created resource dict will be stored in the internal resources dict.
The id it will take may be a serial number, a field or a part of a field, a random number (like a GUID).

The method generate_new_id will return the id for the resource knowing the resource_dict of the resource to be created.

.. literalinclude:: /samples/basicpasswordfile.py
    :pyobject: BasicPasswordFileManager.generate_new_id

The objects can be created and are persisted.
When an object is created, the napixd returns a 201 created code and
send the URI of the newly created resource in the Location header ::

    >> post /passwords/ password=whiterabbit username=tanderson
    {
     username = tanderson
     password = whiterabbit
     }
    $ cat /tmp/test
    sony_bigboss:password3
    sony_rssi:s4fr34$er-
    tanderson:whiterabbit

At this moment, it is possible to create, delete, modify, list and retrieve the resource of our manager.
But there is no validation and it could lead to injection, flaws, etc.

For example if an attacker wants to create a Mallory account, he can set his password to something with a ``\n`` in it.
The ``\n`` cannot be written from the command line.
But napix client will use an external editor if no arguments are given::

    >> put /passwords/sony_bigboss
     1 {
     2   "#_napix_info": [
     3     "Napix Editor.",
     4     "Quit with exit code different from 0 to cancel (:cq in vim)",
     5     "Use the JSON syntax.",
     6     "keys begining by a # are ignored. Like this one."
     7   ],
     8   "password": "a\nmallory:password",
     9   "username": "sony_rssi"
    10 }
    :wq
    >> get /
    [
        /passwords/mallory
        /passwords/sony_bigboss
        /passwords/tanderson
        /passwords/sony_rssi
    ]

.. note::

   The editor can be set with the environment variable :envvar:`$EDITOR`.

He has created an access for Mallory with the password y.
On another hand, the password are way too weak (No wonder why sony got owned by LulzSec).

We have to write validation methods.
In Napix There is three places to make validation of user input.

First, the manager may implement a method called
:meth:`~base.Manager.validate_resource_FIELDNAME` with ``FIELDNAME`` being a field of the resource.
This method is used to clean each field individually.

.. literalinclude:: /samples/basicpasswordfile.py
    :lines: 17,63-78

Now the managers responds with a 400 Error code when we submit a forged password.::

    >> put /passwords/sony_bigboss
     1 {
     2   "#_napix_info": [
     3     "Napix Editor.",
     4     "Quit with exit code different from 0 to cancel (:cq in vim)",
     5     "Use the JSON syntax.",
     6     "keys begining by a # are ignored. Like this one."
     7   ],
     8   "password": "a\np:pouet",
     9   "username": "sony_rssi"
    10 }
    #Save and quit
    :wq
    #The editor reopens and this line appears
    11 //Password cannot contain `\n`
    :cq

Secondly, the manager has a method :meth:`~base.Manager.validate_resource`
which verifies the whole resource dict.

In our case, we can implement a verification to avoid that the password contains the username

.. literalinclude:: /samples/basicpasswordfile.py
    :pyobject: BasicPasswordFileManager.validate_resource

Download the whole python module here: :download:`/samples/basicpasswordfile.py`
