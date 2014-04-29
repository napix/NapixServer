#!/usr/bin/env python
# -*- coding: utf-8 -*-


from napixd.exceptions import NotFound, ValidationError, Duplicate
from napixd.http.response import HTTPError, HTTP405


class MethodMixin(object):
    """
    Mixin for the request where the property **method**
    of the request defines which method is actually used.

    The upper case indexes of :attr:`METHOD_MAP` are considered to be
    HTTP methods and appears in the :meth:`available_methods` and in the
    *Allow* header of returned 405 errors.

    Lower case methods are internal methods and should be used when applicable
    by setting the :attr:`method` before calling :meth:`get_callback`, for
    example by overriding this method.
    Lower case methods are not used in the 405 errors.

    .. attribute:: METHOD_MAP

        A mapping of strings to strings.

        The index is the name of a method, ie an HTTP method like GET,
        and the value is the name of a property of the manager.

    .. attribute:: method

        The current method of the current request.

        This property may be updated by the sub classes before calling
        :meth:`get_callback` if another method is more suitable.

    """
    METHOD_MAP = {}

    def __init__(self, *args, **kw):
        super(MethodMixin, self).__init__(*args, **kw)
        self.method = self.context.method

    @classmethod
    def available_methods(cls, manager):
        """
        Return the HTTP methods defined in the given manager
        that are usable with this :class:`MethodMixin`.
        """
        available_methods = []
        implemented = manager.implements()
        for meth, callback in cls.METHOD_MAP.items():
            if meth.isupper() and callback in implemented:
                available_methods.append(meth)
        return available_methods

    def get_callback(self):
        """
        Retrieves the method we'll call using :attr:`METHOD_MAP` and the user input
        (ie the HTTP method used on the request).

        When the :attr:`method` is not in :attr:`METHOD_MAP`, a *405 METHOD NOT ALLOWED*
        HTTP error is raised with the allowed methods computed by :meth:`available_methods`.
        """
        try:
            return getattr(self.manager, self.METHOD_MAP[self.method])
        except (AttributeError, KeyError):
            raise HTTP405(self.available_methods(self.manager))


class HTTPMixin(object):
    """
    Mixin used with :class:`napixd.services.request.base.ServiceRequest`
    that enables HTTP operations.
    """

    def handle(self):
        """
        Handle the request and calls :meth:`serialize` on the request.

        It catches errors thrown by the managers and translate them in HTTP status codes.
        """
        try:
            result = super(HTTPMixin, self).handle()
            return self.serialize(result)
        except ValidationError as e:
            raise HTTPError(400, dict(e))
        except NotFound as e:
            raise HTTPError(404, u'`{0}` not found'.format(unicode(e)))
        except Duplicate as e:
            raise HTTPError(409, u'`{0}` already exists'.format(
                unicode(e) or u'object'))

    def serialize(self, result):
        """
        Serialize the *result* into something meaningful.

        This has to be implemented by the subclasses.
        """
        raise NotImplementedError()
