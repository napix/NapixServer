.. _auto-loading:

============
Auto Loading
============

Napix proposes a feature that allow to develop and test easily.
A directory in the :file:`HOME` directory.

This feature is enabled by default by the **auto** :ref:`option<options>`.

At the start of the napixd server, a :class:`napixd.loader.importers.AutoImporter`
is added to the :meth:`loaders<napixd.launcher.Setup.get_loaders>`.

This loader will detect all python source files (ending by *.py*),
and try to import them.
Once imported, the loader will browse the module to find
:class:`napixd.managers.base.Manager` subclasses.

The loader check the presence of the `auto_load` attribute on each manager. If true, the manager
class is added to the root services of the server.

.. _reloading:

Auto-reloading
==============

The napixd server can follow the activity of the auto-loaded modules
and reload them if their source files have been modified.

This feature is enabled by default by the **notify** :ref:`option<options>`
and requires the :mod:`pyinotify` library and that the host machine supports inotify
(most recent Linux kernels do).


Errors
======

Errors during the import may occur, such as :exc:`NameError`, :exc:`SyntaxError`, etc.

If the error occurs during the first import, either when the server starts or when
the file has been created and is detected for the first time, it is ignored.

If the error occurs on an module that was already loaded,
the manager affected by the error are removed from the service,
and a :meth:`catch-all rule<napixd.application.NapixdBottle.register_error>`
is added in the application.
This catch-all rule serves all the requests previously served by the manager,
and raises the error that prevented the manager to be loaded.


