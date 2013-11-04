#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
==================
Views on resources
==================

The Napix views allow the resources to be presented differently.

By default, a JSON presentation of the resource is returned.
When a resource implements views, it can return different formats.
For example, it can send a pdf file, a png image, a CSV file, etc.

Views may be added to a managed by implementing a instance method
decorated by :meth:`view`.


Callback
========

The signature of the decorated view is::

    formatter( self, resource, response)

self
    is the instance of the manager.
resource
    The :class:`napixd.services.wrapper.ResourceWrapper` of the requested resource.
    This resource is not filtered and additional fields not declared in
    :data:`~napixd.managers.Manager.resource_fields` are included.
response
    an empty :class:`napixd.http.Response` object.
    This object permits to set headers with
    :meth:`~napixd.http.Response.set_header` and fill the body of the response
    with :meth:`~napixd.http.Response.write`.


If the value returned by the callback is *response* or ``None``,
the response object is returned.
Else the returned value is JSON-encoded as-is and transmitted to the client.

In all cases, the headers set on the *response* object are transmitted.

Usage
=====

The following example show how to encode some data as a CSV document.
The method **view_as_csv** return the *response* object,
so the Napix server will forward this to the client.

.. code-block:: python

    @view('csv')
    def view_as_csv( self, resource_id, resource, response):
        "Dump the race as a CSV file"
        response.set_header('Content-Type', 'text/csv' )
        response.write( '"Firstname";"Lastname";"laps";"avg time";"min time"' )
        for line in resource['lines']:
            response.write(
                '"{firstname}";"{lastname}";"{laps}";"{avg}";"{min}"'.format(
                    lastname=line['lastname'], firstname=line['firstname'],
                    laps = len(line['laps']),
                    avg=len(line['laps']) / sum(line['laps']),
                    min=min(line['laps'])))
        return response

The following examples show the usage of the *response* object as a ``file`` object.
The methods return ``None``. The server will use the *response* object.

.. code-block:: python
    :emphasize-lines: 7,19

    import reportlab
    import PIL

    @view('pdf')
    @content_type('application/pdf')
    def export_as_pdf( self, resource_id, resource, response):
        doc = reportlab.platypus.SimpleDocTemplate( response,
                pagesize=reportlab.lib.pagesizes.A4,
                rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=18,
                title='file.pdf'
        doc.build( self._pdf_story( resource) )

    @view('png')
    @content_type('image/png')
    def export_as_png( self, resource_id, resource, response):
        image = PIL.Image.new( 'RGB', (200, 200), color)
        draw = PIL.ImageDraw.Draw(image)
        draw.text( (50,50), resource_id)
        image.save(response, 'png')

In those examples, the view returns a dictionnary.
Those dict will be JSON encoded and transmitted.

The depreciation warning header will be sent to the client, even if the response object is not used for the body.

.. code-block:: python

    @view('v1')
    def compat_v1( self, resource_id, resource, response):
        " Compatibility layer with the Version 1 of the API "
        #foo has changed name to bar
        response.set_header( 'x-depreciation-warning', '1')
        resource['foo'] = resource['bar']

        #foobar was not implemented
        del resource['foobar']

        #resource will be dumped as JSON
        return resource

    @view('v2')
    def actual_version( self, resource_id, resource, response):
        return resource

"""

import functools

__all__ = ('view', 'content_type')


def view(format):
    """

    Declares a view function.

    The ``format`` parameter is the name of the format that the view returns.
    It is recommended to use the file extension even though it is not mandatory.

    .. note::

        It is recommended to set the Content-Type header of the returned file
        as it is **not** guessed, neither from the format parameter,
        nor from the content of the response.

        The :func:`content_type` helper is available to set it easily
    """
    if not isinstance(format, basestring):
        raise TypeError('format must be a string')
    if format == '':
        raise ValueError('format must not be empty')

    def inner(fn):
        fn._napix_view = format
        return fn
    return inner


def content_type(content_type):
    """
    Convenience decorator to use with view to set the content-type.

    .. code-block:: python

        @view('csv')
        @content_type( 'text/csv' )
        def view_as_csv( self, resource, response):
            #...
    """
    def inner(fn):
        @functools.wraps(fn)
        def wrapper(self, resource, response):
            response.set_header('Content-Type', content_type)
            return fn(self, resource, response)
        return wrapper
    return inner
