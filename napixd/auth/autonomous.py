#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hmac
import hashlib

__all__ = [
    'AutonomousAuthProvider',
]


def decode(value):
    if isinstance(value, unicode):
        value = value.encode('utf-8')
    return value


class AutonomousAuthProvider(object):
    """
    This class implements the central protocol in local.

    A local password is associated with a local username. If the request is
    emitted by the local username, this providers will responds authoritatively.
    Else it will let the other providers decide.

    When the user using the local username emitted the request, he signed with
    a shared password. The hash is checked with the password and if it matches,
    the request is granted.

    Users authenticated by the :class:`AutonomousAuthProvider` are granted all
    the requests.
    """
    @classmethod
    def from_settings(cls, settings):
        login = settings.get('login', 'local_master')
        password = settings.get('password', None)
        if not password:
            raise ValueError(u'password cannot be empty. Set Napix.auth.password')
        return cls(login, password)

    def __init__(self, login, password):
        self.login = login
        self.password = decode(password)

    def __call__(self, request, content):
        if content.get('login') != self.login:
            # Not our login, carry on
            return None
        if content.get('signature', None) == self.sign(content.get('msg', '')):
            # Authorize unconditionally
            return True
        return False

    def sign(self, msg):
        msg = decode(msg)
        return hmac.new(self.password, msg, hashlib.sha256).hexdigest()
