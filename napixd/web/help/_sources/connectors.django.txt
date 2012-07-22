
.. module:: connectors.django

====================
Connector for django
====================


.. class:: DjangoImport( module=None )

    Context Manager used to initialize django before importing a model.

    If ``module`` is not specified, it defaults to the configuration key `Napix.connectors.django`.

    If ``module`` ( or the configuration key) is a string, it will be used as the module name to
    the settings module of the django application (cf ``DJANGO_SETTINGS_MODULE``).
    Else it must be a mapping which keys are used to configure django
    (cf :meth:`django.conf.settings.configure`).

    .. code-block:: python

        from napixd.connectors.django import DjangoImport

        with DjangoImport( 'myproject.settings''):
            from myapp.models import MyModel


.. class:: DjangoReadOnlyModelManager

    Subclass of :class:`managers.Manager` which is specified for a django model.

    .. attribute:: model

        The :class:`django.db.models.Model` used for this manager.

    .. attribute:: model_fields

        Iterables of the included model fields.

        If specified, only the fields of the model given in this set will be used.

    .. attribute:: model_fields_exclude

        Like :attr:`model_fields`, but explicitely exclude the fields.
        When both are specified, model_fields_exclude has the precedence.

    .. attribute:: resource_fields

        Resource fields of this manager. See :attr:`managers.Manager.resource_fields`.

        This attribute is computed from the meta of the model.

        If the class defines its own resource_fields, it is merged with the
        resource_fields generated.
        The additional fields are added, the content of existing fields is merged.

        To remove fields from resource_fields, use :attr:`model_fields_exclude`.

        .. code-block:: python

            class Account( models.Model ):
                number = models.CharField(max_lentgh=200, help_text='Person owning this account' )
                owner = models.CharField( max_lentgh=1000)
                creation_date = models.DateField( auto_now_add=True)

            class BankAccountManager( DjangoReadOnlyModelManager ):
                model = Account
                resource_fields = {
                    'owner' : {
                        'description' : 'Customer of the bank to wich the account is attached.'
                    },
                    'balance' : {
                        'description' : 'Amount of money in this account'
                        'computed' : True
                    }
                }

            BankAccountManager.resource_fields
            {
                'number' : {
                    'description' : 'Customer of the bank to wich the account is attached.'
                },
                'owner' : {
                    'description' : 'Person owning this account',
                },
                'balance' : {
                    'description' : 'Amount of money in this account'
                    'computed' : True
                }
                'creation_date' : {
                    'description' :  '',
                    'computed' : True
                }
            }


    .. attribute:: queryset

        A django queryset or manager.

        When this property is not defined, it's the default manager of :attr:`model` .

    .. method:: get_queryset

        Returns a copy of :attr:`queryset`.

        Can be overridden to return a custom queryset

    .. classmethod:: get_name

        Returns the lower case model name.

    .. method:: get_resource

        Get a resource by its pk.

    .. method:: list_resource

        List the pk of the resource.

.. class:: DjangoModelManager

    Sub class of :class:`DjangoReadOnlyModelManager`
    which adds the modification/deletion/creation operations.

    .. method:: modify_resource

    .. method:: create_resource

    .. method:: delete_resource

.. class:: DjangoRelatedModelManager


    Sub class of :class:`DjangoModelManager`
    which is suitable for a related object.

    Those manager are intended to be used as managed_class
    of a Manager of the related model.

    .. method:: detect

        Override :meth:`~managers.Manager.detect` to always return false.
        This manager is supposed to be used inside a managed_class and get a model as its parent.

    .. attribute:: related_to

        The model or the name of the model to which this manager is related.

        .. code-block:: python

            class PollManager(DjangoModelManager):
                model = Poll

            class AnswerManager(DjangoRelatedModelManager):
                model = Answer
                related_to = Poll

    .. attribute:: related_by

        The name of the relation.

        It is required if there is more than one relation between the two models.

