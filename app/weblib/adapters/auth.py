#!/usr/bin/env python
# -*- coding: utf-8 -*-

import oauth2


__all__ = ['OAuthAdapter', 'AlwaysFailOAuthAdapter',
           'AlwaysSuccessOAuthAdapter']


class OAuthAdapter(object):
    """Defines an adapter of the OAuth authentication layer.
    
    Using this instead of direct calls to the library make it possible to
    execute integration tests without reaching the requested oauth endpoints.
    """

    def create_client(self, clientid, clientsecret):
        return oauth2.Client(oauth2.Consumer(clientid, clientsecret))


class AlwaysFailOAuthAdapter(object):
    """Defines an OAuth adapter always returning a 501 error."""

    def create_client(self, clientid, clientsecret):
        class Client(object):
            def request(self, url, method):
                return ({'status': '501'}, 'Internal server error')
        return Client()


class AlwaysSuccessOAuthAdapter(object):
    """Defines an OAuth adapter always returning a 200 error."""

    def create_client(self, clientid, clientsecret):
        class Client(object):
            def request(self, url, method):
                return ({'status': '200'}, 'OK')
        return Client()
