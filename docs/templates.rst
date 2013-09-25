.. program:: napixd-template

==========================
The napix Templates system
==========================

Napix proposes a command to create quickly a manager.

The :program:`napixd-template` lets you create a manager file in the
:ref:`auto-loading` directory.

usage::

    napixd-template
    napixd-template template_name
    napixd-template -n destination_name
    napixd-template --name destination_name template_name

This forms create the destination file specified by :option:`-n` with the given template.

If there is no template given, **default** is used.
The *default* templates contains a base :class:`napixd.managers.base.Manager`
with all the features, :ref:`validation`, :ref:`views`, :ref:`actions`, etc.

The template must be an existing template
The list of all existing template may be queried with the :option:`--list`::

    napixd-template --list


.. option:: --list, -l

   Lists all the availables templates and exits.

.. option:: --name, -n

   Sets the name of the destination.
   If the name already exists, a suffix *_n* is happened with a incremental *n*
   so the file does not overwrite an existing.

   By default the name is *my_manager*.
