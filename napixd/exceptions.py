#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['PermissionDenied','ValidationError']
# FIXME : pourquoi on ne met pas NotFound et Duplicate dans __all__ ?


class PermissionDenied(Exception):
    pass
class ValidationError(Exception):
    pass
class NotFound(Exception):
    pass
class Duplicate(Exception):
    pass
