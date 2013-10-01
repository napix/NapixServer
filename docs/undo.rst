.. currentmodule:: napixd.utils.undo


============
Undo Manager
============

The undo manager feature of Napix proposes a facility
to register callbacks in case of an exception to cancel the side-effects.

Callbacks
=========
The callbacks are added by the method :meth:`~UndoManager.register`
They do not take any argument.

.. code-block:: python

   def step1():
       """Write Hello in file.txt"""
       handle = open('file.txt', 'w')
       handle.write('hello\n')
       handle.close()

    def undo_step1():
       """Remove file.txt"""
       os.unlink('file.txt')

   um = UndoManager()
   step1()
   um.register(undo_step1)


Exceptions happening inside the callback are silently ignored.

The :class:`UndoManager` executes the callbacks in the reverse order in which they have been registered.

Automatic rollback
==================

The :class:`UndoManager` is a context manager which catches exceptions
and calls the callbacks if an exception is raised inside the context and not caught.

.. code-block:: python

   um = UndoManager()

   with um:
        # if any of the step* method raises,
        # the UndoManager calls the register undo_step* methods
        step1()
        um.register(undo_step1)
        step2()
        um.register(undo_step2)
        step3()


Manual rollback
===============

The rollback can be manually triggered with :meth:`UndoManager.undo`.

.. code-block:: python

   um = UndoManager()

   with um:
        # if any of the step* method raises,
        # the UndoManager calls the register undo_step* methods
        step1()
        um.register(undo_step1)
        step2()
        um.register(undo_step2)

        if not step3():
            # triggers the undo manually if step3 returns False
            um.undo()


