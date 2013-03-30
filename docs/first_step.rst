.. highlight:: python

.. currentmodule:: napixd.managers

.. _first_step:

=======================================
First steps in the writing of a manager
=======================================

In Napix, managers behaves like collection and have the logic to maintain a set of resources.

Napix uses the REST approach: an URI defines a resource and HTTP verbs ( GET, PUT, POST, etc) defines the action on it.
``PUT /htaccess/toto`` is used to modify the resource identified by /htaccess/toto with the data given in the request body.
``GET /htaccess/toto`` is used to retrieve the same resource.
``GET /htaccess/tata`` retrieves another resource.

Napix uses :class:`~base.Manager` subclasses to handle the collections logic.
Each Manager instance represents a collection and provides methods to manage the collection.
Managers are listed in the top level of the URI, eg, ``GET /htaccess/toto`` will ask to the manager *htaccess* the resource *toto*.

Launch
======

The first step is to launch the server as described in :ref:`installation`.
Install pyinotify to enable the auto-reloading (so you don't have to Ctrl+C / rerun all the time), and the napix client to query the server::

    (napix)$ pip install pyinotify
    (napix)$ pip install http://builds.enix.org/napix/NapixCLI-latest.tar.gz

If you pay attention to napixd output, you'll see some valuable information when you start it :

- pid (Starting process xx),
- used ``HOME`` directory (Found napixd home at /xxx),
- fullpath of the log file ( Logging activity in /xxx),
- the listening socket ( Listening on http://xxx:xxx/).

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

You can check that the server is up and responding by poking it with NapixCLI command line interface, called ``napix`` ::

    $ napix -s localhost:8002
    >> ls
    [ ]

.. note::

   If you followed the :ref:`quickstart`, you'll see ``[ /hello ]`` as you installed HelloWorld Manager in :ref:`helloworld`.

Write a manager
===============

Best way to understand how Napix works is to get your hands dirty, so we'll see how to write a little plain text password manager step by step.

.. note::

   The examples below use snippets from different sources :

    If there is no prompt, the snippet is from the example manager ``HOME/auto/password.py``

    A ``(napix)$`` indicates a shell with the virtualenv loaded::

    (napix)$ napixd noauth

    A ``>>`` indicates an interactive session within the napix client::

        (napix)$ napix -s localhost:8002
        >> get /

    A ``>>>`` indicates an interactive python shell

        (napix)$ python
        >>> import os


The auto-loader directory is the auto folder inside the ``HOME`` directory, by default in ``~/.napixd/auto``.

Launch your favorite editor with and open a file in the auto-load directory ``~/.napixd/auto/password.py``.
Write the headers and save.

.. literalinclude:: /samples/basicpasswordfile.py
    :lines: 1-2

The autoloader will detect the filesystem operation and launch a reload.
A line ``Reloading`` will appear in the log of the napixd daemon console you've previously launched::

    (napix)$ napixd nodoc debug print_exc noauth nonotify
    [...]
    INFO:Napix.reload:Caught file change, reloading
    INFO:Napix.conf:Using /home/krystal/.napixd/conf/settings.json configuration file
    Reloading
    INFO:Napix.console:Reloading


A curl request will still show an empty array, because we didn't write any manager (yet!) in the file::

    >> get /
    [ ]

Continue writing in the previously opened file.

.. literalinclude:: /samples/basicpasswordfile.py
    :lines: 6

The :class:`default.DictManager` class is a subclass of :class:`~base.Manager`
which simplifies the way of writing a Manager.
Instead of writing a method to make a modification, retrieve a resource, create it, etc,
the :class:`~default.DictManager` instance store an internal dict of all its resource indexed by their id.
The :class:`~default.DictManager` implements the method to modify, create, list, etc and does the operation on the internal dict,
so you just have to define a load and a save method to get things working (and an id generator, which we'll explain later).

Append the following lines in the password.py file.

.. literalinclude:: /samples/basicpasswordfile.py
    :lines: 12-15

When you save the file, the daemon will reload the managers and find the one you created.
A GET request will show you it.::

    >> get /
    [
        /basicpasswordfile
    ]

.. note::
    You'll probably need to restart your napix client as it cache request by default.

If you make a mistake while writing a manager, and cause the import to fail, Napix will forgive you.
Just correct the error and save.
When an import fails, and makes a manager unavailable, a placeholder will catch the calls and
return the error that cause the import to fail so you can get useful output in the CLI.

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

Now, we have a manager, but we didn't tell napix how we want to handle our ``resources`.
Any attempt to list the resources (using GET /``name of the manager``/) fails with a :exc:`NotImplementedError`::

    >> get /basicpasswordfile/
    Napixd Error NotImplementedError

    [...]

    /home/napix/NapixServer/napixd/managers/default.py in _get_resources
        67   self._resources = self.load(self.parent)

    /home/napix/NapixServer/napixd/managers/default.py in load
        63   raise NotImplementedError, 'load'

    NotImplementedError: load


.. note::

  You can observe here the behavior of Napix when an uncaught exception is raised.
  It returns a 500 error, with the description of the exceptions serialized in JSON.

To fix this, we need to :

- describe the resource we want to manage, by specifying its fields and their description in the manager's metadatas
- write a load method to populate the internal dict we use in our ``DictManager``


The metadata
------------

The metadatas of the Manager are composed of the docstring of the module
which should describe what kind of resources it manages, and the :attr:`~base.Manager.resource_fields` attribute
which documents the field's name of the managed resources and metadatas about them.

Metadatas are necessary so napix can auto-document your manager, and are used for basic filtering of users' input.
The resources that are sent to the user are stripped of the fields that are not in the `resource_fields`
and the resource_dict given to the creation and modification method contains only fields in resource_fields.

In our example, we also define a class constant.
We can also use a configuration option, but it requires to use the configuration loader
and not the auto loader.
See more details about the configuration in :ref:`configuration`.

.. literalinclude:: /samples/basicpasswordfile.py
    :lines: 16,21-30

The resources of our manager will contain two field, a ``username`` and a ``password``.
In the description, we comment our field to explain what they'll contain (quite obvious here),
and we give an example a valid value. Example is used to build a template of the ressource, which
can then be used by napixd client to help user fill correctly the resource.

.. note::

The template object can be retrieved at ``/basicpasswordfile/_napix_new``::

    >> get /basicpasswordfile/_napix_new
    {
        password: toto42
        username: john
    }

By default, the url namespace is class name, in lower case.
It can be changed by overriding the classmethod :meth:`~base.Manager.get_name`.

.. literalinclude:: /samples/basicpasswordfile.py
    :lines: 32-34

The requests show that the old name is gone replaced by the new one.::

    >> get /
    [
        /passwords
    ]
    >> get /passwords/_napix_new
    {
        "password": "toto42",
        "username": "john"
    }


Loading datas
-------------

To get our internal dict populated, we'll override the :meth:`~default.DictManager.load` method.

The load method takes one parameters : the parent manager.
It can be used to write multi level manager, eg if we wanted to edit multiple files,
we could have written a manager that list the files, and then instanciate a BasicPasswordFileManager for each file found.
Anyway, in our case, we don't use this, and as our manager is a *first level* manager (directly under /), parent is set to :obj:`None`.

The inheritance cases are treated in :ref:`inheritance`.
;; FIXME not working

.. literalinclude:: /samples/basicpasswordfile.py
    :lines: 4,12,16,36-49

Now the manager can be listed and consulted::

    $ echo 'bigbro_rssi:pikachu1' > /tmp/test
    $ echo 'bigbro_bigboss:password3' >> /tmp/test
    >> get /passwords/
    [
        /passwords/bigbro_rssi
        /passwords/bigbro_bigboss"
    ]
    >> get /passwords/bigbro_rssi
    {
        password: pikachu1
        username: bigbro_rssi
    }

.. note::
    The manager is instancied at each call, so you don't have to reload napix when you modify the file externally.
    But as we don't check for lock and don't do any locking, this example is not safe for concurrent editing.

Still, as we don't write yet a :meth:`~default.DictManager.save` method, any attempt to modify an existing object will fail.::

    >> put /passwords/bigbro_rssi password=s4fr34$er- username=bigbro_rssi
    Napixd Error NotImplementedError
    
    [ ... ]
    
    /home/napix/NapixServer/napixd/managers/default.py in end_request
        130   self.save(self.parent,self.resources)

    /home/napix/NapixServer/napixd/managers/default.py in save
        112   raise NotImplementedError, 'save'

    NotImplementedError: save


Save Method
-----------

Save takes two arguments :

- the parent (the same as in load), which we can ignore again as we are directly under the root
- a dict, which contain the resources, so we can make this data persistent.

.. literalinclude:: /samples/basicpasswordfile.py
    :pyobject: BasicPasswordFileManager.save

Now the result is persisted::

    >> put /passwords/bigbro_rssi password=s4fr34$er- username=bigbro_rssi
    $ cat /tmp/test
    bigbro_bigboss:password3
    bigbro_rssi:s4fr34$er-
    >> get /passwords/
    [
        /passwords/bigbro_bigboss
        /passwords/bigbro_rssi
    ]

.. tip::
   You can edit the resource with your favorite :envvar:`$EDITOR`. (get from environnement) if you don't specify any key=value value in your put::

      >> put /passwords/bigbro_rssi
      [ ... editor get executed and modify the file ... ]
      [ ... resource is saved ...]
      >> get /passwords/bigbro_rssi
      {
       username = bigbro_rssi
       password = password_from_editor
       }


But if we try to create a resource, with a POST request, this will fail miserably ::

    >> post /passwords/ password=neo username=tanderson
    Napixd Error NotImplementedError

    [...]

    /home/napix/NapixServer/napixd/managers/default.py in create_resource
        148   resource_id = self.generate_new_id(resource_dict)

    /home/napix/NapixServer/napixd/managers/default.py in generate_new_id
        119   raise NotImplementedError, 'generate_new_id'

    NotImplementedError: generate_new_id


This is due to the need for every resource in your manager to be identified by an unique id. Napixd has no way
to guess how you want to discriminate your ressource, so it ask for you to do so, by writing a :meth:`~default.DictManager.generate_new_id`, which get the resource_dict as a parameters, and have to return an unique id.
You could return anything, like a serial number, a random string, or something 
generated from the resources field, but remember that you'll have to save it in your persistent storage.

In our manager, as we don't want multiple user with same login, we'll use the username field to generate the id.

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
    bigbro_bigboss:password3
    bigbro_rssi:s4fr34$er-
    tanderson:whiterabbit

At this moment, it is possible to create, delete, modify, list and retrieve the resource of our manager.
But there is no validation and could lead to injection, flaws, etc.

For example if an attacker wants to create a ``mallory`` account, he can set his password to something with a ``\n`` in it ::

    >> put /passwords/bigbro_bigboss
     1 {
     2   "#_napix_info": [
     3     "Napix Editor.",
     4     "Quit with exit code different from 0 to cancel (:cq in vim)",
     5     "Use the JSON syntax.",
     6     "keys begining by a # are ignored. Like this one."
     7   ],
     8   "password": "a\nmallory:rogueaccount",
     9   "username": "bigbro_rssi"
    10 }
    :wq
    >> get /
    [
        /passwords/mallory
        /passwords/bigbro_bigboss
        /passwords/tanderson
        /passwords/bigbro_rssi
    ]

.. tip::

   The editor can be set with the environment variable :envvar:`$EDITOR`.

He has created an access for ``mallory`` with the password ``rogueaccount`` due to the way we internally persist the data on disk.
To prevent that, we have to write some kind of validation. And as we don't want our user to use weak password, we'll add a little
check to force them to use more than 6 chars.

In Napix, there is two places to validate the user's input:
each field and the whole object.

First, the manager may implement a method called
:meth:`~base.Manager.validate_resource_FIELDNAME` with ``FIELDNAME`` being a field of the resource.
This method is used to clean each field individually.

.. literalinclude:: /samples/basicpasswordfile.py
    :lines: 7,17,63-78

Now the managers responds with a 400 Error code when we submit a forged password.::

    >> put /passwords/bigbro_bigboss
     1 {
     2   "#_napix_info": [
     3     "Napix Editor.",
     4     "Quit with exit code different from 0 to cancel (:cq in vim)",
     5     "Use the JSON syntax.",
     6     "keys begining by a # are ignored. Like this one."
     7   ],
     8   "password": "a\np:pouet",
     9   "username": "bigbro_rssi"
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
