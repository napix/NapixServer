
.. module:: executor

========
Executor
========

The Napix server provides tools to run and manage processes and threads.

According to the posix standard, it is not recommended to launch processes from a thread which is not the main thread.
In order to work around this limitation Napix provides a tool that runs in the main thread,
wait for requests from other threads, launches the process and return the handler.
The tool also keeps a trace of running processes.



.. data:: executor

    The :data:`executor` attribute of :mod:`executor` is an instance of :class:`Executor`.
    The :class:`Executor` class should not be instantiated, and this instance should be used instead.

.. class:: Executor

    The executor is a wrapper around subprocess that manages the running processes.
    The process is removed from the list once it has terminated.

    .. method:: create_process( command, discard_output=True) -> handler

        Add a new process in the queue, and wait for it to be processed.

        The `command` is a list starting with the target executable
        followed by the list of the arguments of this target.
        This is comparable with the standard library :mod:`subprocess` module.

        When `discard_output` is true, the :attr:`~ExecHandle.stdout` and :attr:`~ExecHandle.stderr` of the running process
        are sent to :file:`/dev/null`.

        This method returns a :class:`ExecHandle` object.

    .. method:: run

        Launch the executor.

        When the executor is running, it listens to an internal queue for job requests,
        it launch the process and returns by a async queue the handle.

        This method is blocking and returns after :meth:`stop` has been called.

    .. method:: stop

        Ask to the control thread of the executor.

        It will stop all the processes running.

        This method returns immediately and actual stopping will run in another thread asynchronously.

.. class:: ExecHandle

        The handlers objects are wrappers around :class:`subprocess.Popen`.

        The main added feature is the notification of the executor.
        Because the executor keeps a trace of all running processes, the wrapper has to notify the executor
        via an asynchronous queue when it ended.

        It proxies the :class:`subprocess.Popen` object and has the same properties :attr:`return_code`, :meth:`wait`, :meth:`poll`, etc.

    .. method:: kill

        Kills the process.

        It sends the process a SIGTERM, waits for 3 seconds for the process to stop, then it send a SIGKILL and returns.
