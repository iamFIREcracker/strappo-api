#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web


def api(func):
    """Checks that the current request has the header ``HTTP_ACCEPT`` set and
    that the specified value is actually supported by the server.

    If an unsupported content-type is passed, a '406 Not acceptable' is sent
    back to the client.

    On success, the requested content-type header is set and the request is
    executed.

    >>> class MyNotAcceptable(Exception):
    ...   pass
    >>> web.notacceptable = MyNotAcceptable
    >>> request = lambda: 'Hello world'

    >>> web.ctx['environ'] = dict()
    >>> web.ctx['headers'] = list()
    >>> api(request)()
    Traceback (most recent call last):
        ...
    MyNotAcceptable

    >>> web.ctx['environ'] = dict(HTTP_ACCEPT='application/xml')
    >>> web.ctx['headers'] = list()
    >>> api(request)()
    Traceback (most recent call last):
        ...
    MyNotAcceptable

    >>> web.ctx['environ'] = dict(HTTP_ACCEPT='application/json')
    >>> web.ctx['headers'] = list()
    >>> api(request)()
    'Hello world'
    """
    def inner(*args, **kwargs):
        accept = web.ctx.environ.get('HTTP_ACCEPT', '').split(',')
        if 'application/json' not in accept:
            raise web.notacceptable()

        return func(*args, **kwargs)
    return func if web.config.DISABLE_HTTP_ACCEPT_CHECK else inner

def internal(ips):
    def inner(func):
        def inner2(*args, **kwargs):
            remote = web.ctx.environ.get('REMOTE_ADDR', '')
            if remote not in ips:
                raise web.forbidden()

            return func(*args, **kwargs)
        return inner2
    return inner


def authorized(func):
    """Checks that an authorized user has been successfully associated with the
    request.

    The decorator checks the 'current_user' property of the request controller:
    if that contains a valid object, then the request gets marked as authorized,
    otherwise a '401 Unhauthorize' error message is sent back to the client.

    >>> from mock import MagicMock
    >>> from mock import Mock
    >>> class MyUnauthorized(Exception):
    ...   pass
    >>> web.unauthorized = MyUnauthorized
    >>> request = lambda *a: 'Hello world'

    >>> authorized(request)(Mock(current_user=None))
    Traceback (most recent call last):
        ...
    MyUnauthorized

    >>> authorized(request)(Mock())
    'Hello world'
    """
    def inner(self, *args, **kwargs):
        if not self.current_user:
            raise web.unauthorized()

        return func(self, *args, **kwargs)
    return inner
