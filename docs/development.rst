.. currentmodule:: napixd.managers

**********************
Development with Napix
**********************

Napix is a framework designed to simplify development of modules.
The framework targets the sysadmin world.

.. include:: deployment.txt

=========================================
Consideration about writing a new Manager
=========================================

Manager / DictManager / ListManager
===================================

.. currentmodule:: napixd.managers

All managers in Napix are sub-classes of :class:`base.Manager`.
Napix proposes a set of classes inheriting of this class and exposing another interface.

To select the best suited interface for your project,
you should consider the way the resources data and their ID are fetched.

When the resources are all fetched and written in one block,
for example by parsing a file,
the :class:`default.DictManager` is the best suited interface.
It exposes a :meth:`default.DictManager.load` method to
retrieve all the resources and a :meth:`default.DictManager.save` method
to persist them all.

When the resources are fetched one by one, for example DB record,
then the classic :class:`base.Manager` class is better.
It exposes 5 methods that handle
:meth:`listing<base.ManagerInterface.list_resource>`,
:meth:`fetching<base.ManagerInterface.get_resource>`,
:meth:`creation<base.ManagerInterface.create_resource>`,
:meth:`modification<base.ManagerInterface.modify_resource>` and
:meth:`deletion<base.ManagerInterface.delete_resource>`.

MutiManager
===========

Managers can be stacked.
A stacked manager depends on the resource of the previous manager.

**Usecases**: A DNS server manager has a list of zones.
There is a zone manager. Inside the zone there are records.
The zone manager gets a record manager stacked inside.


The link between the manager and its parent
-------------------------------------------

If the stacked manager requires to modify the resource of the parent manager,
or call methods, etc, then it's recommended to use a object instead of a dict in the parent.

The resource as returned by :meth:`base.Manager.get_resource` or
:meth:`default.DictManager.load` is an object and the method
:meth:`base.Manager.serialize` transform it into a dict.

This will produce better looking code than doing query on a dict
and help with type checking, etc.

===========================
Writing the resource fields
===========================

Napix requires that the managers declare the fields owned by the objects
they produce and they receive.
The resource_fields writing step is important in Napix as it forces
the developper to lay his ideas and it serves as a first prototyping.

The :attr:`~base.Manager.resource_fields` are listed as a :class:`dict` in the class.
Each resource field is a :class:`dict` of the options and the meta data about this field.

Read only fields
================

When prototyping or in development or by choice, you can declare fields read-only.
The read-only fields are filtered in the input but still appear in the ouptut.

The :attr:`~resource_fields.ResourceField.computed` property
declares a field read-only.

Meta data
=========

You can add any meta-data to your fields, including *display_order* or *description*.
Values not recognized by the server are stored in the meta dict.
:attr:`~resource_fields.ResourceField.extra` and recopied
in the *_napix_help* section.
Those values serves as a hint for the generic web interface, the users or the other developpers.

=====================
Howto write a manager
=====================

.. _dev-manager:

.. currentmodule:: napixd.managers.base

:class:`Manager` class
======================

The :class:`Manager` is the base class of all managers.
The managers may implement these 5 methods:
:meth:`~Manager.list_resource`,
:meth:`~Manager.get_resource`,
:meth:`~Manager.create_resource`,
:meth:`~Manager.modify_resource` and
:meth:`~Manager.delete_resource`.

Each method is linked to a REST feature.
Implementing :meth:`~Manager.create_resource`
will allow the *POST* method on the collection.

The implementation of the methods is not required.
If the manager does not implement the method the feature will simply be removed.

A manager requires at least one :attr:`~Manager.resource_fields`.

.. code-block:: python

    from napixd.managers import Manager


    class CPUFreqManager(Manager):
        """ A cpufreq utility """

        resource_fields = {
            'governor': {
                'description': 'The cpufreq governor',
                'example': 'ondemand',
            },
            'frequency': {
                'description': 'The frequency of the cpu in Hz',
                'example': 1199000,
            }
        }


:meth:`~Manager.list_resource`
------------------------------

This method list all the ids of the resources in the system.
If fetching the ids also retrieves the objects content,
a :ref:`dev-dictmanager` is more suited.

.. code-block:: python

    def expand_file(self, path):
        with open(path) as handle:
            return self.expand(handle.read())

    def expand(self, pattern):
        ids = list()
        for range in pattern.split(','):
            if '-' in range:
                first, last = range.split('-', 1)
                ids.extend(xrange(int(first), int(last) + 1))
            else:
                ids.append(int(range))
        return ids

    def list_resource(self):
        return sorted(self.expand_file('/sys/devices/system/cpu/online'))

:meth:`~Manager.get_resource`
-----------------------------

This method fetches a single object by its id.
If you cannot fetch a single object but must retrieve them all,
a :ref:`dev-dictmanager` is more suited.

If the object does not exists, raise a :exc:`napixd.exceptions.NotFound`.
This error will be transformed as a **404 Not Found**.

The method should return a :class:`dict`.
The keys that are not present in the :attr:`~Manager.resource_fields`
are stripped from the dict.
The values should be serializable in JSON (:class:`int`, :class:`float`, :class:`str`,
:class:`unicode`, :class:`list` and :class:`dict`).

It can return another object of any class (except ``None``)
but it must then provide a :meth:`Manager.serialize`
method to transform this object in a JSON.
See :ref:`dev-serialize` for more details.

The id comes directly from the url.
The id has its URL encoded characters decoded.
You can add a :meth:`Manager.validate_id` method that takes the user's id
and transforms it into a better suited representation or
performs sanity and security checks.

.. code-block:: python

    def validate_id(self, cpu_id):
        try:
            return int(cpu_id)
        except ValueError:
            raise ValidationError('cpu id have the cpuN format')

    def get_r serversource(self, cpu_id):
        #cpu_id is validated by validate_id
        #it is safe to use it directly
        if cpu_id not in self.expand_file('/sys/devices/system/cpu/online'):
            raise NotFound(cpu_id)
        cpu_path = os.path.join('/sys/devices/system/cpu/', 'cpu{0}'.format(cpu_id))
        governor_path = os.path.join(cpu_path, 'scaling_governor')
        frequency_path = os.path.join(cpu_path, 'scaling_cur_freq')

        with open(frequency_path) as frequency_handle:
            frequency = int(frequency_handle.read())
        with open(governor_path) as governor_handle:
            governor = governor_handle.read().strip()

        return {
            'governor': governor,
            'frequency': frequency,
        }

:meth:`~Manager.create_resource`
--------------------------------

It creates a new resource.
The method takes a dict as argument and returns the ID.

The resource dict given have been validated by the validation mechanism
described in detail in the section :ref:`validation`

If a resource cannot be created, because the target ID is already taken,
the :exc:`napixd.exceptions.Duplicate` should be raised.
The server will return a **409 conflict** response.

Once the server has created the resource it must return the ID
of the newly created resource.

.. code-block:: python

    def create_resource(self, resource_dict):
        presents = self.expand_file('/sys/devices/system/cpu/present')
        offlines = self.expand_file('/sys/devices/system/cpu/offline')
        ids = set(presents).intersection(offlines)
        if not ids:
            raise Duplicate('No available CPU is present')
        cpu_id = ids.pop()
        cpu_path = os.path.join('/sys/devices/system/cpu/', 'cpu{0}'.format(cpu_id))
        offline_file = os.path.join(cpu_path, 'online')
        governor_path = os.path.join(cpu_path, 'scaling_governor')
        frequency_path = os.path.join(cpu_path, 'scaling_cur_freq')
        with open(offline_file, 'wb') as handle:
            handle.write('1\n')
        with open(frequency_path, 'wb') as frequency_handle:
            frequency_handle.write('{0}\n'.format(resource_dict['frequency']))
        with open(governor_path, 'wb') as governor_handle:
            frequency_handle.write('{0}\n'.format(resource_dict['governor']))
        return cpu_id

:meth:`~Manager.delete_resource`
--------------------------------

This method deletes a resource by it's id.
The methods takes a :class:`napixd.services.wrapper.ResourceWrapper`
as its first argument.
The resource wrapper is an object designed to transfert a resource,
its ID and the manager which produced it to methods, actions, views, submanagers, etc.

The :attr:`~napixd.services.wrapper.ResourceWrapper.id` property of the resource
is the ID validated by :meth:`~Manager.validate_id`.
The resource is lazily loaded in the wrapper.
The first access to :attr:`~napixd.services.wrapper.ResourceWrapper.resource`
will fire a call to the :meth:`get_resource` of the
:attr:`~napixd.services.wrapper.ResourceWrapper.manager` which is responsible
for the fetching.

This method is not expected to return anything.

.. warning:: The existence is not checked.

   The manager has not yet checked the existence of the resource.
   You can do it yourself in the method or use the :attr:`resource` property
   of the *resource_wrapper*.

.. code-block:: python

    def delete_resource(self, resource_wrapper):
        online = self.expand_file('/sys/devices/system/cpu/online')
        if resource_wrapper.id not in online:
            raise NotFound(resource_wrapper.id)
        cpu_path = os.path.join('/sys/devices/system/cpu/', 'cpu{0}'.format(resource_wrapper.id))
        offline_file = os.path.join(cpu_path, 'online')
        with open(offline_file, 'wb') as handle:
            handle.write('0\n')

:meth:`~Manager.modify_resource`
--------------------------------

This method performs a transformation on a resource.
The method gets a :class:`napixd.services.wrapper.ResourceWrapper`
and a :class:`napixd.managers.changeset.DiffDict`.

The resource wrapper contains the resource and the id.
The resource has been fetched and exists.

.. currentmodule:: napixd.managers.changeset

The diffdict is a :class:`collections.Mapping`.
It contains all the validated fields of the resource submitted by the user.
The dict also has properties containing the changes between the original object
and the proposed objects:
:attr:`DiffDict.added` for the values in the input that are not in the original,
:attr:`DiffDict.changed` for the values that are present but not the same and
:attr:`DiffDict.deleted` for the values removed from the original.

If the resource changes its ID as a result of the modification,
the method should return the new ID.
If the ID has changed,
The server will issue a *205* HTTP response to indicate a URL change.
When id does not change, returning None or the same ID  triggers a *204* response.

.. code-block:: python

    def modify_resource(self, resource_wrapper, diffdict):
        cpu_id = resource_wrapper.id
        cpu_path = os.path.join('/sys/devices/system/cpu/', 'cpu{0}'.format(cpu_id))
        if 'frequency' in diffdict.changed:
            frequency_path = os.path.join(cpu_path, 'scaling_cur_freq')
            with open(frequency_path, 'wb') as frequency_handle:
                frequency_handle.write('{0}\n'.format(diffdict['frequency']))
        if 'governor' in diffdict.changed:
            governor_path = os.path.join(cpu_path, 'scaling_governor')
            with open(governor_path, 'wb') as governor_handle:
                frequency_handle.write('{0}\n'.format(diffdict['governor']))


.. _dev-dictmanager:
.. currentmodule:: napixd.managers.default

class :class:`DictManager`
==========================

Napix propose a different way to write managers.
The :class:`DictManager` uses 2 methods, one to load all the objects
and one to save them all.

The :attr:`DictManager.resource_fields` are the same a the :class:`Manager`.

There is a :class:`ReadOnlyDictManager` which only implements
the GET method, :meth:`ReadOnlyDictManager.list_resource` and
:meth:`ReadOnlyDictManager.get_resource`.

.. warning::

   All the objects exists at the same time in the memory.
   If there is a lot of objects or objects are heavy,
   you should rather use a classic :ref:`dev-manager`.

.. code-block:: python

    from napixd.managers.default import DictManager


    class NSSwitchManager(DictManager):
        """Napix manager for nsswitch.conf"""
        resource_fields = {
            'sources': {
                'example': [
                    'compat'
                ],
                'description': 'The sources for each database'
            },
            'database': {
                'editable': False,
                'choices': [
                    'aliases',
                    'ethers',
                    'group',
                    'hosts',
                    'initgroups',
                    'netgroup',
                    'networks',
                    'passwd',
                    'protocols',
                    'publickey',
                    'rpc',
                    'services',
                    'shadow',
                ],
            }
        }

:meth:`DictManager.load`
------------------------

This method returns the resources as a :class:`dict`.
The keys are the ids of the resources.
The values are :class:`dict` with the content of the resource.
It also can be a object provided that the manager has a :meth:`DictManager.serialize`
method transforming this object in a :class:`dict`.

.. code-block:: python

    def load(self, parent):
        resources = {}
        with open('/etc/nsswitch.conf', 'rb') as nsswitch:
            for line in nsswitch:
                line = line.strip()
                if not line or line.startswith('#') or not ':' in line:
                    continue
                database, sources = line.split(':', 1)
                resources[database] = {
                    'database': database,
                    'sources': sources.split(),
                }
        return resources

:meth:`DictManager.save`
------------------------

This method takes the parent and the resources and persists them.
When the manager is the first manager of the stack, the parent is ``None``.

the :class:`DictManager` requires a :meth:`DictManager.generate_new_id`
that returns the ID from a user's input.
The ID can be extracted from the dict or generated from
a external sequence or randomly generated, etc.

.. code-block:: python

    def generate_new_id(self, resource):
        return resource['database']

    def save(self, parent, resources):
        with open('/etc/nsswitch.conf', 'wb') as nsswitch:
            for id, resource in resources.items():
                if not resource:
                    continue
                nsswitch.write('{0}: {1}\n'.format(id, ' '.join(resources['sources']))


.. include:: validation.txt

================
Advanced Manager
================

Propriété particuliere ?
versionning
objet requete
userid ?

.. include:: extensions.txt

.. include:: submanagers.txt

id, parent, etc
lazy
resultat du get_resource
appel autre manager
ne pas faire !
si vraiment besoin, exemple aver wrapping d’objet

Specials listing methods
========================

.. currentmodule:: napixd.managers.base

:meth:`Manager.get_all_resources`
---------------------------------

:meth:`Manager.list_resource_filter`
------------------------------------


.. _dev-serialize:

Serialization
=============

Napix works natively with :class:`dict`.
They are serialized a JSON and sent thought the HTTP layer.

Using Python objects and classes is possible.
This is useful with stacked managers.
When :meth:`Manager.get_resource` returns an object that is not a :class:`dict`,
it must also implement a :class:`Manager.serialize`.

This method takes the original object (or the dict) and return the object
to transfer in JSON.

.. code-block:: python

    class Pie(object):
        def __init__(self, flavor):
            self.flavor = flavor

        @property
        def taste(self):
            if self.flavor in ('apple', 'chocolate'):
                return 'good'
            elif self.flavor in ('pear', 'peach', 'apricot'):
                return 'meh'
            elif self.flavor in ('cucumber', 'bean'):
                return 'bad'

    class ThingManager(DictManager):
        resource_fields = {
            'flavor': {
                'example': 'good'
            }
        }
        def load(self, parent):
            return {
                'apple': Pie('apple'),
                'cucumber': Pie('cucumber')
            }
        def serialize(self, pie):
            return {
                'flavor': pie.flavor
            }


Modifications
-------------

When modifying with :meth:`Manager.modify_resource`,
the original object untouched is passed as the :attr:`ResourceWrapper.resource`
and the serialized version is used by the :class:`DiffDict`.


