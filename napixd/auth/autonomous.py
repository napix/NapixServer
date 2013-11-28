#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hmac
import hashlib

__all__ = ('AutonomousAuthProvider', )


def decode(value):
    if isinstance(value, unicode):
        value = value.encode('utf-8')
    return value


class AutonomousAuthProvider(object):
    """
    This class implements the central protocol in local.

    Requests signature is checked with the same hmac mechanism as the central does.
    The requests is then granted if the signature matches else it's refused.
    """
    @classmethod
    def from_settings(cls, settings):
        login = settings.get('login', 'local_master')
        password = settings.get('password', None)
        if not password:
            raise ValueError('password cannot be empty. Set Napix.auth.password')
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
