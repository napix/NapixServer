#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Unique identifier of this Napix Instance

NapixID is stored in :file:`HOME/napixd_id`.

.. data:: uid

    An instance of :class:`NapixID` wich contains the identifier
    for the running Napix instance.
    The ID will stay the same between two runs of this instance.

    The ID will change on the same server if used with another **HOME**.

"""


__all__ = ('NapixID', 'uid')

import uuid
import logging

from napixd import get_file

logger = logging.getLogger('Napix.GUID')

open = open


class NapixID(object):

    """
    The loader of uniquer identifier.

    The uniquer identifier is an instance of :class:`uuid.UUID` accessible
    with the property :attr:`uuid` or in a string form by calling :class:`str`
    on this object.

    The Unique identifier is lazily loaded by the first access to :attr:`uuid`.
    It may raise a :exc:`ValueError` if the :file:`napixd_id` file exists but
    does not contains a valid :class:`~uuid.UUID`.
    """

    def __init__(self):
        self.id_file = get_file('napixd_id')
        self._napix_id = None

    def __str__(self):
        return str(self.uuid)

    @property
    def uuid(self):
        """
        The Unique identifier.
        """
        if self._napix_id is None:
            self._load_or_gen()
        return self._napix_id

    def _load_or_gen(self):
        uid = self.load()
        if uid is not None:
            self._napix_id = uid
            return self._napix_id

        self._napix_id = self.gen()
        self.save()
        return self._napix_id

    def gen(self):
        return uuid.uuid4()

    def save(self):
        logger.info('Saving UUID in %s', self.id_file)
        try:
            handle = open(self.id_file, 'wb')
            with handle:
                handle.write(str(self._napix_id))
        except IOError, e:
            logger.exception(e)

    def load(self):
        logger.debug('Loading UUID from %s', self.id_file)
        try:
            handle = open(self.id_file, 'rb')
        except IOError, e:
            return None

        try:
            return uuid.UUID(handle.read().strip())
        except (IOError, ValueError) as e:
            logger.exception(e)
            raise ValueError('Cannot read the ID')
        finally:
            handle.close()

uid = NapixID()
