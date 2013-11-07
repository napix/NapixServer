===============
Manager Locking
===============

Napix proposes a feature to isolate operations on a group of Napix servers.
This feature uses a Redis server to share the locks.

Configuration
=============

The shared lock server is configured by the section :ref:`conf.napix.lock`.

Usage
=====

The locks are used by the :class:`~napixd.services.Service`

.. code-block:: python

    @synchronized('lock-name')
    class ThingManager(Manager):
        resource_fields = {
            'foo': {
                'example': 'bar'
            }
        }
        def get_resource(self, id):
            # retrieve the resource
            # wont run in the same times as other process




