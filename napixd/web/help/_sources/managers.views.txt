
.. module:: managers.views

==================
Views on resources
==================

The Napix views allow the resources to be presented differently.

By default, a JSON presentation of the resource is returned.
When a resource implements views, it can return different formats.
For example, it can send a pdf file, a png image, a CSV file, etc.

Views may be added to a managed by implementing a instance method
decorated by :meth:`view`.

.. decorator:: view( format)

    Declares a view function.

    The ``format`` parameter is the name of the format that the view returns.
    It is recommended to use the file extension even if it is not a constraint.

    .. note::

        It is recommended to set the Content-Type header of the returned file
        as it is **not** guessed, neither from the format parameter,
        nor from the content of the response.

    The signature of the decorated view is::

        formatter( self, resource_id, resource, response)

    ``self`` is the instance of the manager.

    ``resource_id`` is the resource id of the requested resource.
    This id has been validated by :meth:`~managers.Manager.validate_id`
    if it has been implemented.

    ``resource`` is the resource asked to be formatted.
    This resource is not filtered and additional fields not declared in
    :data:`~managers.Manager.resource_fields` are included.

    ``response`` is a :class:`http.Response` object.

    The docstring of the decorated method is used to describe the formatter in the auto-documentation.

    If the view returns ``None`` or the ``response`` parameter, the latter will be used.

    If it returns something else, the content of the response will be ignored
    and the object returned will be JSON encoded.

    For example, to show a export a CSV dump of a resource
    Note that there is no return, so the response object is used.

    .. code-block:: python

        @view('csv')
        def view_as_csv( self, resource_id, resource, response):
            """Dump the race as a CSV file"""
            response.set_header('Content-Type', 'text/csv' )
            response.write( '"Firstname";"Lastname";"laps";"avg time";"min time"' )
            for line in resource['lines']:
                response.write(
                    '"{firstname}";"{lastname}";"{laps}";"{avg}";"{min}"'.format(
                        lastname=line['lastname'], firstname=line['firstname'],
                        laps = len(line['laps']),
                        avg=len(line['laps']) / sum(line['laps']),
                        min=min(line['laps'])))

    The `response` parameter can be used with PIL :meth:`Image.save` or reportlab :class:`SimpleDocTemplate`.

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

    This other example shows a use case for return.

    .. code-block:: python

        @view('v1')
        def compat_v1( self, resource_id, resource, response):
            """
            Compatibility layer with the Version 1 of the API
            """
            #foo has changed name to bar
            resource['foo'] = resource['bar']

            #foobar was not implemented
            del resource['foobar']

            #resource will be dumped as JSON
            return resource

        @view('v2')
        def actual_version( self, resource_id, resource, response):
            return resource

.. decorator:: content_type( content_type )

    Convenience decorator to use with view to set the content-type.

    .. code-block:: python

        @view('csv')
        @content_type( 'text/csv' )
        def view_as_csv( self, resource, response):
            #...
