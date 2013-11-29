
.. _notify:

========================
Napix Directory Protocol
========================

Napix has a protocol used by all the servers from a domain
to signal their existence to a directory server.
The protocol relies on the Napix protocol, including auth.

Notification Protocol
=====================

All the servers notify their existence by sending a POST request to the directory.
The POST request returns a *201* response and a *Location* header.

Then at each 300 second interval, the server send a PUT request to this *location*.
The timeout is then refreshed.

All the server that have notified the server in the last 600s are **OK**.
If the last notification of the server is between 600 and 900 seconds old,
the server is categorized as **WAITING**.
Then up to 6600 seconds its **LOST**.
After the server is removed from the list.

Directory Server
================

The directory server is an regular instance of napixd.
It loads a :class:`napixd.contrib.directory.NapixDirectoryManager`.

This manager uses the :ref:`storage`  facility of Napix to keep tracks of the servers.

Notification Client
===================

.. currentmodule:: napixd.notify

Each server having to notify launches a :class:`Notifier`.
The notifies starts in background and send request at regular intervals.
