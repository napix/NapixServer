
.. module:: managers.default


Default Managers
================


This module provides some classes to implements default strategies for managers.

They will load all the resources of the manager, allow the user to make requests
and persist all the objects after.


.. class:: ReadOnlyDictManager

    Sub class of :class:`managers.Manager` that will preload a dictionary as its resources.
    The access to this resources is read-only, ie GET.

    The only method to override is :meth:`load`.

    .. attribute:: resources

        The resources attribute is the content of the manager.
        It is lazily loaded with the :meth:`load` method.

    .. method:: load( parent ) -> dict[ resource_id : resource_dict]

        Load: Return the list of the resources managed by this manager
        take the parent that created this manager instance as argument

        The `parent` argument is the parent resource from which the manager is instantiated

        example:

        .. code-block:: python

            class CountryManager(ListManager):
                """
                Load the countries of a planet
                """
                resource_fields = {
                        'name' : {
                            'description' : 'name of the country',
                        },
                        'population' : {
                            'description' : 'number of person living in the country',
                        }
                    }

                def load(self,parent):
                    #The parent is the planet resource
                    f=open('/'+parent['galaxy']+'/'+parent['planet'],'r')
                    countries = []
                    for x in f.readline():
                        countries.append(x)
                    return x

            #GET /worlds/earth/france
            parent = WorldManager().get_resource('earth')
            parent
            World { 'name':'planet', 'galaxy': 'Milky Way'}

            earth_countries = CountryManager(parent)
            earth_countries.get_resource('france')

            earth_countries.load({'name':'earth','galaxy':'Milky Way'})

.. class:: DictManager

    Subclass of :class:`ReadOnlyDictManager` that is also accessible in write, ie DELETE, POST and PUT.

    The methods :meth:`ReadOnlyDictManager.load`, :meth:`save` and :meth:`generate_new_id` must be overridden.
    The first read the content of the manager, the second persist it, and the last find a new id when it is needed (POST).

    The :ref:`validation methods <validation>` of :class:`managers.Manager` are used.

    .. method:: save( parent, resources)

        Save the ressources after they have been altered by the user's request.
        Idempotent methods (GET,HEAD) don't trigger the save

        The `parent` argument is the same argument that was passed to the load method,
        and contains the parent resource to which this manager is attached.

        The `resources` argument is the instance of :attr:`ReadOnlyDictManager.resources`.

        .. code-block:: python

            class CountryManager(ListManager):
                def save(self,parent,ressources):
                    f=open('/'+parent['galaxy']+'/'+parent['planet'],'w')
                    countries = []
                    for x in resources:
                        countries.write(x)
                        countries.write('\n')


    .. method:: generate_new_id( resource_dict ) -> new_id

        Return a new id for the given `resource_dict`


