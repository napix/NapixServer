#!/usr/bin/env python
# -*- coding: utf-8 -*-


from napixd.exceptions import NotFound, ValidationError, Duplicate
from napixd.http.response import HTTPError, HTTP405


class MethodMixin(object):
    METHOD_MAP = {}

    def __init__(self, *args, **kw):
        super(MethodMixin, self).__init__(*args, **kw)
        self.method = self.context.method

    @classmethod
    def available_methods(cls, manager):
        """
        Return the HTTP methods defined in the given manager
        that are usable with this ServiceRequest
        """
        available_methods = []
        for meth, callback in cls.METHOD_MAP.items():
            if meth.isupper() and hasattr(manager, callback):
                available_methods.append(meth)
        return available_methods

    def get_callback(self):
        """
        Retreive the method we'll call using self.METHOD_MAP and the user input
        (ie the HTTP method used on the ressource)

        Return 405 if the request is not implemented.
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
        Actually handle the request.
        Call a set of methods that may be overrident by subclasses.
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
