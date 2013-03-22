.. currentmodule:: napixd.connectors.django

===================
Using Django models
===================

Napixd allows users to plug with django.
Because of the centralized configuration of an django application,
it's only possible to use a single configuration file.


Using existing django application
=================================

Assuming a existing django application `polls` installed in mysite,
as in the django tutorial.

The :file:`polls/models.py` is as such:

.. code-block:: python

    from django.db import models

    class Poll(models.Model):
        question = models.CharField(max_length=200)
        pub_date = models.DateTimeField('date published')

    class Choice(models.Model):
        poll = models.ForeignKey(Poll)
        choice_text = models.CharField(max_length=200)
        votes = models.IntegerField()

We wish to enable a web service with Napix.

We create a :file:`services.py` inside the application `polls`.

In order to import the models from :file:`polls/models.py`, django needs to be set up.
We need to use the :class:`DjangoImport`.
This class used as a Context Manager will set up the django environment for the import.
We give it the settings module, here ``mysite.settings``.

.. code-block:: python

    from napixd.connectors.django import DjangoImport

    with DjangoImport('mysite.settings'):
        from polls.models import Poll, Choice

The django connector provides also specialized :class:`~managers.Manager` subclasses
when a model instance is mapped to a manager.

The class :class:`DjangoModelManager` is used for a first level manager,
and :class:`DjangoRelatedModelManager` for the managed_classes.
They take a :attr:`~DjangoReadOnlyModelManager.model` class attribute
which is a :class:`django.db.models.Model` class.

.. code-block:: python

    from napixd.connectors.django import DjangoRelatedModelManager, DjangoModelManager

    class PollManager( DjangoModelManager):
        model = Poll

The :attr:`managers.Manager.resource_fields` dict is automatically computed.
The class attributes :attr:`~DjangoReadOnlyModelManager.model_fields` and
:attr:`~DjangoReadOnlyModelManager.model_fields_exclude` control the fields included or excluded,

Additional non-model fields can be added in the resource_fields dict,
and if the existing description of fields is merged with the one computed.

.. code-block:: python

    class PollManager( DjangoModelManager):
        model = Poll

    PollManager.resource_fields
    {
        "question" : {
            "description" : "",
            "computed" : False
        },
        "pub_date" : {
            "description" : "",
            "computed" : False
        }
    }

    class CustomPollManager( DjangoModelManager):
        model = Poll
        resource_fields = {
            "total_votes" : {
                "description" : "Total number of votes"
            },
            "question" : {
                "example" : "Tea or Coffee?"
            },
            "pub_date" : {
                "description" : "Date of the publication"
            }
        }

    CustomPollManager.resource_fields
    {
        "question" : {
            "description" : "",
            "computed" : False,
            "example" : "Tea or Coffee?"
        },
        "pub_date" : {
            "description" : "Date of the publication"
            "computed" : False
        },
        "total_votes" : {
            "description" : "Total number of votes"
        }
    }

The managed class Manager requires an additional :attr:`~DjangoRelatedModelManager.related_to` or :attr:`~DjangoRelatedModelManager.related_by`
to describe the relation between the parent and the children.


.. code-block:: python

    class PollManager( DjangoModelManager):
        model = Poll
        managed_class = [ 'ChoiceManager' ]

    class ChoiceManager(DjangoRelatedModelManager):
        model = Choice
        related_to = Poll

Using Django models for the storage
===================================

Another use case of django is using the models for the storage.

The conf can be written inline, inside the configuration file.
Django has a centralised configuration management and it is impossible to load
multiple configuration in the same Napix instance.

:class:`DjangoImport` raises an exception when it have to load different configurations files,
but it supports loading (or reloading) multiple uses with the same configuration.

.. code-block:: python

    from napixd.connectors.django import DjangoImport, DjangoModelManager
    importer = DjangoImport({
            "DATABASES" : {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": "/home/napix/sqlitedb"
                }
            }
    })
    with importer:
        from django.db import models

    class MyModel( models.Model ):
        key = models.CharField( max_length=124)
        value = models.IntegerField()

    class MyManager( DjangoModelManager):
        model = MyModel


.. note::

    Keep in mind that the syncdb command is not included in this configuration.
    You have to create the tables manually.
