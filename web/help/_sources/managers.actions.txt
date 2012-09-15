.. module:: managers.actions

Actions
=======

Action are arbitrary python function that can be called on a resource of a collection.

.. decorator:: action

    Decorates a python function that will be an action

    The action takes the resource as its first argument.

    The decorator automatically discovers the mandatory and optional arguments of the function
    and use them for documentation and template request generation.

    .. code-block:: python

        class RouterManager( Manager ):
            resource_fields = {
                    'ip' : {
                        'description' : 'IP of the target router'
                    }
                }
            ...
            @action
            def ping(self, router, tries=3):
                for x in tries:
                    if ping( router['ip']):
                        return 'Router responds'
                return 'Router Unreachable'

.. decorator:: parameter

    Allow to set one or several parameters on an action.

    .. code-block:: python

        @parameter( 'tries',  description = 'Number of times we try to ping' )
        @action
        def ping(self, router, tries=3):
            for x in tries:
                if ping( router['ip']):
                    return 'Router responds'
            return 'Router Unreachable'


