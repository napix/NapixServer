.. highlight:: python

.. currentmodule:: managers.default

.. _first_step:

=======================================
First steps in the writing of a manager
=======================================

In Napix, managers behaves like collection and have the logic
to maintain a set of resources.

Napix uses the REST approach: an URI defines a resource and HTTP verbs ( GET, PUT, POST, etc) defines the action on it.
PUT /htaccess/toto is used to modify the resource identified by /htaccess/toto with the data given in the request body.
GET /htaccess/toto is used to retrieve the same resource.
GET /htaccess/tata retrieves another resource.

Napix uses :class:`~managers.Manager` subclasses to handle the collections logic.
Each Manager instance represents a collection and provides methods to manage the collection.

Launch
======

The first step is to launch the server as described in :ref:`installation`.
Install pyinotify to enable the auto-reloading.::

    (napix)$ pip install pyinotify

When launching the napixd daemon, it shows its PID (Starting process xx),
its root directory (Found napixd home at /xxx),
the log file ( Logging activity in /xxx),
the socket on which it is listening ( Listening on http://xxx:xxx/).

The server can be stopped by hitting Ctrl+c, and it may take up to 3 seconds to stop.::

    (napix)$ bin/napixd
    Starting process 1482
    Found napixd home at /home/user/NapixServer
    Logging activity in /tmp/napix.log
    Bottle server starting up (using RocketAndExecutor())...
    Listening on http://0.0.0.0:8002/
    Hit Ctrl-C to quit.

You can check that the server is up and responding by poking it with curl.  ::

    $ curl -D /dev/stderr -X GET "localhost:8002/?authok" -s | python -m json.tool
    HTTP/1.1 200 OK
    Content-Length: 54
    Content-Type: application/json
    Date: Thu, 14 Jun 2012 10:26:43 GMT
    Server: Rocket 1.2.4 Python/2.6.6
    Connection: keep-alive

    [ ]

``curl``
    A classic command line HTTP client.
``-D /dev/stderr``
    Tells to curl to show the HTTP headers.
``-X GET``
    Sends a GET request
``"localhost:8002/?authok"``
    The host and url on which curl will send its request.
    The authok GET parameter is a bypass of the napix authentication, while Napix run in debug mode.
``-s``
    tells to curl to be silent and thus avoids the progress bar.
``| python -m json.tool``
    Formats the output as a human readable json object.


Write a manager
===============

The auto-loader directory is the auto-folder inside the root directory.
Here it is /home/user/NapixServer/auto.

Launch your favorite editor with and open a file in the auto-load directory :file:`vim /home/user/NapixServer/auto/password.py`.
Write the headers and save.

.. literalinclude:: /samples/basicpasswordfile.py
    :lines: 1-2

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

A curl request will still show an empty array, because there isn't a Manager yet to be loaded.

Continue writing in the previously opened file.

.. literalinclude:: /samples/basicpasswordfile.py
    :lines: 6

The :class:`DictManager` class is a subclass of :class:`~managers.Manager`
which simplifies the way of writing a Manager.
Instead of writing a method to make a modification, retrieve a resource, create it, etc,
the DictManager instance store an internal dict of all its resource indexed by id.
The DictManager implements the method to modify, create, list, etc and does the operation on the internal dict.

Append the following lines in the password.py file.

.. literalinclude:: /samples/basicpasswordfile.py
    :lines: 12-15

When you save the file, the daemon will reload the managers and find the one you created.
A curl GET request will show you it.::

    $ curl -X GET "localhost:8002/?authok" -s | python -m json.tool
    [
        "/basicpasswordfilemanager"
    ]

If you make a mistake while writing a manager, and it causes the import to fail, Napix will forgive you.
Just correct the error and save.
If an import fails, and makes a manager unavailable, a placeholder will catch the calls and
return the error that cause the import to fail.

For example: add a syntax error or a undeclared name in the file.

.. code-block::

    class BasicPasswordFileManager(DictOopsIMadeAMistake):
        """
        Napix server to edit a password file in the user:password format
        """

The requests will fail with an :exc:`ImportError` caused by a :exc:`NameError`::

    $ curl -X GET "localhost:8002/basicpasswordfilemanager?authhok" -s | python -m json.tool
    {
        "error_class": "ImportError",
        "error_text": "NameError(\"name 'DictOopsIMadeAMistake' is not defined\",)",
        "filename": "/home/dude/NapixServer/napixd/loader.py",
        "line": 352,
        "request": {
            "method": "GET",
            "path": "/basicpasswordfilemanager"
        },
        "traceback": []
    }

Rollback to fix this error before continuing.

An attempt to list the resources (using GET /``name of the manager``/) fails with a :exc:`NotImplementedError`
because the load method that the developer must override is not yet written.::

    $ curl -X GET "localhost:8002/basicpasswordfilemanager/?authok" -s -D /dev/stderr | python -m json.tool
    HTTP/1.1 500 Internal Server Error
    Content-Length: 219
    Content-Type: application/json
    Date: Thu, 14 Jun 2012 12:49:23 GMT
    Server: Rocket 1.2.4 Python/2.6.6
    Connection: keep-alive

    {
        "error_class": "NotImplementedError",
        "error_text": "load",
        "filename": "/home/napix/NapixServer/napixd/managers/default.py",
        "line": 51,
        "request": {
            "method": "GET",
            "path": "/basicpasswordfilemanager/"
        },
        "traceback": []
    }

You can here observe here the comportment of Napix when an uncaught exception is raised.
It returns a 500 error, with the description of the exceptions serialized in JSON.

The developer still have to write the metadatas of the manager (its documentation and the field of the resources it manages),
the methods to load and persist the internal dict and a method to tell what is the id of a newly created resource.

The metadata
------------

The metadatas of the Manager are composed of the docstring of the module
which should describe what kind of resources it manages, and the :attr:`~managers.Manager.resource_fields` attribute
which documents the names of the attributes of the managed resources and metadatas about them.

The metadatas of the managers have two main goals.
They take part in the auto-documentation of the manager and for the filtering of the input and output.
The resources that are sent to the user are stripped of the fields that are not in the `resource_fields`
and the resource_dict given to the creation and modification method contains only fields in resource_fields.

.. literalinclude:: /samples/basicpasswordfile.py
    :lines: 16,21-30

The resources of our manager will contain a ``username`` and the corresponding ``password``.
The template object proposed to the users will be ``john:toto42``.

This template object is retrieved at ``/basicpasswordfilemanager/_napix_new``::

    $ curl -X GET "localhost:8002/basicpasswordfilemanager/_napix_new?authok" -s | python -m json.tool
    {
        "password": "toto42",
        "username": "john"
    }

The url namespace is basicpasswordfilemanager.
It is the default value of the lower case class name.
It can be changed by overriding the classmethod :meth:`~managers.Manager.get_name`.

.. literalinclude:: /samples/basicpasswordfile.py
    :lines: 32-34

The requests show that the old name is gone replaced by the new one.::

    $ curl -X GET "localhost:8002/?authok" -s | python -m json.tool
    [
        "/passwords"
    ]
    $ curl -X GET "localhost:8002/passwords/_napix_new?authok" -s | python -m json.tool
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
    $ curl -X GET "http://localhost:8002/passwords/?authok" | python -m json.tool
    [
        "/passwords/sony_rssi",
        "/passwords/sony_bigboss"
    ]
    $ curl -X GET "http://localhost:8002/passwords/sony_rssi?authok" | python -m json.tool
    {
        "password": "pikachu1",
        "username": "sony_rssi"
    }

But an attempt to modify an existing object will fail.::

    $ curl -s -X PUT -H 'Content-Type: application/json' \
        "localhost:8002/passwords/sony_rssi?authok" \
        --data '{"password":"s4fr34$er-","username":"tanderson"}' | python -m json.tool
    {
        "error_class": "NotImplementedError",
        "error_text": "save",
        "filename": "/home/napix/NapixServer/napixd/managers/default.py",
        "line": 107,
        "request": {
            "method": "PUT",
            "path": "/passwords/sony_rssi"
        },
        "traceback": []
    }

Another :exc:`NotImplementedError` this time because we need to override the :meth:`~managers.default.DictManager.save`.
Save takes the parent (the same as in load) and the resources of the managers as argument and persists them to the disk.

Like in the load method, we can ignore the parent argument.

.. literalinclude:: /samples/basicpasswordfile.py
    :pyobject: BasicPasswordFileManager.save

Now the result is persisted::

    $ curl -s -X PUT -H 'Content-Type: application/json' \
        "localhost:8002/passwords/sony_rssi?authok" \
        --data '{"password":"s4fr34$er-","username":"tanderson"}'
    $ cat /tmp/test
    sony_bigboss:password3
    sony_rssi:s4fr34$er-
    $ curl -X GET "http://localhost:8002/passwords/sony_rssi?authok" | python -m json.tool
    {
        "password": "s43fr34$er",
        "username": "sony_rssi"
    }

For the creation of a resource, a POST request is sent to the collection::

    $ curl -s -X POST -H 'Content-Type: application/json' \
        "localhost:8002/passwords/?authok" \
        --data '{"password":"s4fr34$er-","username":"tanderson"}' | python -m json.tool
    {
        "error_class": "NotImplementedError",
        "error_text": "generate_new_id",
        "filename": "/home/napix/NapixServer/napixd/managers/default.py",
        "line": 107,
        "request": {
            "method": "POST",
            "path": "/passwords/"
        },
        "traceback": []
    }

A new NotImplementedError, this one comes from the :meth:`~managers.Manager.DictManager.generate_new_id` method.
In order to create a new resource, the created resource dict will be stored in the internal resources dict.
The id it will take may be a serial number, a field or a part of a field, a random number (like a GUID).

The method generate_new_id will return the id for the resource knowing the resource_dict of the resource to be created.

.. literalinclude:: /samples/basicpasswordfile.py
    :pyobject: BasicPasswordFileManager.generate_new_id

The objects can be created and are persisted.
When an object is created, the napixd returns a 201 created code and
send the URI of the newly created resource in the Location header ::

    $ curl -s -X POST -H 'Content-Type: application/json' \
        "localhost:8002/passwords/?authok" \
        --data '{"password":"whiterabbit","username":"tanderson"}'
    HTTP/1.1 201 Created
    Content-Length: 0
    Location: /passwords/tanderson
    Date: Thu, 14 Jun 2012 17:09:45 GMT
    Server: Rocket 1.2.4 Python/2.6.6
    Connection: keep-alive

    $ cat /tmp/test
    sony_bigboss:password3
    sony_rssi:s4fr34$er-
    tanderson:whiterabbit

At this moment, it is possible to create, delete, modify, list and retrieve the resource of our manager.
But there is no validation and it could lead to injection, flaws, etc.

For example if an attacker wants to create a Mallory account, he can set his password to something with a \n in it.::

    $ curl -s -X PUT -H 'Content-Type: application/json' \
        "localhost:8002/passwords/sony_bigboss?authok" \
        --data '{"password":"x\nmallory:y","username":"sony_bigboss"}' -D /dev/stderr
    HTTP/1.1 200 OK
    Content-Length: 0
    Content-Type:
    Date: Thu, 14 Jun 2012 17:17:10 GMT
    Server: Rocket 1.2.4 Python/2.6.6
    Connection: keep-alive

    $ curl -s -X GET  "localhost:8002/passwords/?authok"  | python -m json.tool
    [
        "/passwords/mallory",
        "/passwords/sony_bigboss",
        "/passwords/tanderson",
        "/passwords/sony_rssi"
    ]

He has created an access for Mallory with the password y.
On another hand, the password are way too weak (No wonder why sony got owned by LulzSec).

We have to write validation methods.
In Napix There is three places to make validation of user input.

First, the manager may implement a method called
:meth:`~managers.Manager.validate_resource_FIELDNAME` with ``FIELDNAME`` being a field of the resource.
This method is used to clean each field individually.

.. literalinclude:: /samples/basicpasswordfile.py
    :lines: 17,63-78

Now the managers responds with a 400 Error code when we submit a forged password.::

    $ curl -s -X PUT -H 'Content-Type: application/json' \
        "localhost:8002/passwords/sony_bigboss?authok" \
        --data '{"password":"y\noscar:pass","username":"sony_bigboss"}' -D /dev/stderr
    HTTP/1.1 400 Bad Request
    Content-Length: 29
    Content-Type: text/plain
    Date: Fri, 15 Jun 2012 09:49:43 GMT
    Server: Rocket 1.2.4 Python/2.6.6
    Connection: keep-alive

    Password cannot contain `\n`

Secondly, the manager has a method :meth:`~managers.Manager.validate_resource`
which verifies the whole resource dict.

In our case, we can implement a verification to avoid that the password contains the username

.. literalinclude:: /samples/basicpasswordfile.py
    :pyobject: BasicPasswordFileManager.validate_resource


Download the whole python module here: :download:`/samples/basicpasswordfile.py`
