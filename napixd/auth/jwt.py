#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import json

from napixd.http.response import HTTPError


class JSONWebToken(object):
    """
    Implentation of the JSON Web Token RFC
    """
    def __init__(self):
        self._expected_headers = frozenset([
            'alg',
            'typ',
        ])

    def decode_jwt(self, http_header):
        """
        When validating a JWT the following steps MUST be taken.  The order
        of the steps is not significant in cases where there are no
        dependencies between the inputs and outputs of the steps.  If any of
        the listed steps fails then the JWT MUST be rejected for processing.
        """
        # 1.   The JWT MUST contain at least one period ('.') character.

        # 6.   Determine whether the JWT is a JWS or a JWE using any of the
        #       methods described in Section 9 of [JWE].

        # o  If the object is using the JWS Compact Serialization or the JWE
        #   Compact Serialization, the number of base64url encoded segments
        #   separated by period ('.') characters differs for JWSs and JWEs.
        #   JWSs have three segments separated by two period ('.') characters.
        #   JWEs have five segments separated by four period ('.') characters.

        # Only JWS are supported

        # 2.   Let the Encoded JWT Header be the portion of the JWT before the
        #       first period ('.') character.

        # 7.   Depending upon whether the JWT is a JWS or JWE, there are two
        #       cases:

        #       *  If the JWT is a JWS, all steps specified in [JWS] for
        #       validating a JWS MUST be followed.  Let the Message be the
        #       result of base64url decoding the JWS Payload.

        #       *  Else, if the JWT is a JWE, all steps specified in [JWE] for
        #       validating a JWE MUST be followed.  Let the Message be the
        #       JWE Plaintext.

        # JWS are validated by the authentication servers

        signed_payload, signature = http_header.rsplit('.', 1)
        encoded_jwt_header, encoded_jws_payload = signed_payload.split('.')

        # 3.   The Encoded JWT Header MUST be successfully base64url decoded
        #       following the restriction given in this specification that no
        #       padding characters have been used.

        # 9.   Otherwise, let the JWT Claims Set be the Message.
        try:
            raw_jwt_header = base64.urlsafe_b64decode(encoded_jwt_header)
            raw_body = base64.urlsafe_b64decode(encoded_jws_payload)
        except (ValueError, TypeError):
            return None

        # 4.   The resulting JWT Header MUST be completely valid JSON syntax
        #       conforming to RFC 4627 [RFC4627].
        try:
            jwt_headers = json.loads(raw_jwt_header)
        except ValueError:
            return None

        # 5.   The resulting JWT Header MUST be validated to only include
        #       parameters and values whose syntax and semantics are both
        #       understood and supported or that are specified as being ignored
        #       when not understood.
        if not set(jwt_headers.keys()).issubset(self._expected_headers):
            raise HTTPError(400, 'Unsupported JWT headers: {0}'.format(
                ','.join(set(jwt_headers.keys()).difference(self._expected_headers))))

        # 8.   If the JWT Header contains a "cty" (content type) value of
        #       "JWT", then the Message is a JWT that was the subject of nested
        #       signing or encryption operations.  In this case, return to Step
        #       1, using the Message as the JWT.

        if jwt_headers.get('cty', '').upper() == 'JWT':
            raise HTTPError('Nested Encryption is not supported')

        # 10.  The JWT Claims Set MUST be completely valid JSON syntax
        #       conforming to RFC 4627 [RFC4627].

        try:
            claims = json.loads(raw_body)
        except ValueError:
            raise HTTPError(400, 'Bad JSON values')

        try:
            claims = self._convert(claims)
        except KeyError as e:
            raise HTTPError(400, 'Missing/Misformatted key {0}'.format(e))

        claims.update({
            'msg': signed_payload,
            'signature': signature,
            'is_secure': True,
        })
        return claims

    def _convert(self, claims):
        try:
            method, path = claims.pop('sub').split(' ', 1)
        except ValueError:
            raise KeyError('sub')

        return {
            'method': method,
            'path': path,
            'login': claims['iss'],
            'host': claims['aud'],
            'nonce': claims['jti'],
            'timestamp': claims['exp'],
        }

    def __call__(self, request):
        if 'Authorization' not in request.headers:
            return None

        authorization = request.headers['Authorization']

        if authorization.count('.') != 2:
            return None

        return self.decode_jwt(authorization)
