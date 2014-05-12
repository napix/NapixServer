#!/usr/bin/env python
# -*- coding: utf-8 -*-

from napixd.http.response import HTTPError


class UserAgentDetector(object):
    """
    Display a human readable message when a browser is detected.
    """

    def __call__(self, callback, request):
        if (request.headers.get('user_agent', '').startswith('Mozilla') and
            not request.headers.get('X-Requested-With') == 'XMLHttpRequest' and
                'Authorization' not in request.headers):
            return HTTPError(401, '''
<html>
<head><title>Request Not authorized</title></head>
<body>
<h1> You need to sign your request</h1>
<p>Maybe you wish to visit <a href="/_napix_js/">the web interface</a></p>
</body>
</html>''',
                             content_type='text/html')
        else:
            return callback(request)
