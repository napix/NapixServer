#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The services instantiate a instance of a :class:`ServiceRequest` sub-class
to handle the specific work of a request.
"""

from napixd.services.requests.collection import (
    HTTPServiceCollectionRequest as ServiceCollectionRequest,
)
from napixd.services.requests.resource import (
    HTTPServiceResourceRequest as ServiceResourceRequest,
    HTTPServiceActionRequest as ServiceActionRequest,
    HTTPServiceManagedClassesRequest as ServiceManagedClassesRequest,
)

__all__ = (
    'ServiceResourceRequest',
    'ServiceCollectionRequest',
    'ServiceManagedClassesRequest',
    'ServiceActionRequest',
)
