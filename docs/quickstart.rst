=====================
Set up a Napix Server
=====================

Installation
============

Install the napix server::

    virtualenv napix
    source napix/bin/activate
    pip install http://builds.enix.org/napix/napixd-latest.tar.gz

Run the napix server::

    $ napixd only
    Napixd Home is /home/user/.napixd
    INFO:Napix.console:Napixd Home is /home/user/.napixd
    Options are only
    INFO:Napix.console:Options are only
    Starting process 25367
    INFO:Napix.console:Starting process 25367
    Logging activity in /home/user/.napixd/log/napix.log
    INFO:Napix.console:Logging activity in /home/user/.napixd/log/napix.log
    INFO:Napix.conf:Using /home/user/.napixd/conf/settings.json configuration file
    INFO:Napix.Server:Starting
    Stopping
    INFO:Napix.console:Stopping
    Stopped
    INFO:Napix.console:Stopped

The second line *Napixd Home is* **path** tells what the HOME of Napix is.
Napix finds its configuration, its managers and save its logs and stored files in its HOME.

The HOME can be forced with ``NAPIXHOME`` environment variable.

The :program:`napixd` program takes arguments.
The arguments are options to enable or disable features.
The ``only`` option disable all default options.

The develop setup
=================

In order to develop on napix without being embarrassed with extra features::

    napixd only print_exc times gevent app reload useragent webclient auto

This setup disable authentication and notifications and print the caught exceptions in the console.

You can add python modules in ``HOME/auto``
