.. currentmodule:: napixd.utils.undo


============
Undo Manager
============

The undo manager feature of Napix proposes a facility
to register callbacks in case of an exception to cancel the side-effects.

Usecase
=======

Here is an example of an "efficent use" of :class:`UndoManager`.

.. code-block:: python

    from napixd.utils.undo import UndoManager

    def create_resource(self, userdict):
        """ Process to resource creation """
        def create_tmpfile(undo, id):
            """ Create a tmpfile. Don't use it for real. """
            filename = "/var/lib/my_thing/{0}".format(id)
            handle = open(filename, 'w')

            @undo.register
            def cancel():
                os.unlink(filename)

            return handle

        def use_tmpfile(undo, handle, userdict):
            """ Make use of our temporary file """
            with handle:
                write_or_whatever(handle, userdict)

            def cancel():
                unwrite_or_whatever(handle, userdict)

            undo.register(cancel)

       with UndoManager() as undo:
           id = self.generate_new_id()
           handle = create_tmpfile(undo, id)
           use_tmpfile(undo, handle, userdict)

        return id

Let's see what we've done here :
 - First, we've defined some kind of step for our process, and wrote
   code for it.
 - Then for each step, if there is a point, we defined a :meth:`cancel`
   function and :meth:`~UndoManager.register` it to our :class:`UndoManager`.
   Note how we define this function: inside our step, at the end of it.
   By doing so, we get access to the current namespace, which is full of useful
   variables (handle and namespace here). Then we can use those
   variables without having to carry them in argument.
 - Finally, we use our :class:`UndoManager` as a context manager via the ``with``
   statement. When used like this, :class:`UndoManager` will execute in a
   reversed order every functions that where registered if an exception
   is raised.



Callbacks
=========
The callbacks are added by the method :meth:`~UndoManager.register`
They do not take any argument. We recommend you to define your undo
method by closure as seen in the previous topic.

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


Exceptions happening inside the callback are logged and discarded.

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

If you don't want to raise manually an exception, you can rollback
by mannually triggering :meth:`UndoManager.undo`.

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


