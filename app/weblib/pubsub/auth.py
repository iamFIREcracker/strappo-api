#!/usr/bin/env python
# -*- coding: utf-8 -*-


from app.weblib.pubsub import Publisher


class InSessionVerifier(Publisher):
    """
    >>> class Subscriber(object):
    ...   def session_contains(self, key, value):
    ...     print 'Contains: %(key)s=%(value)s' % dict(key=key, value=value)
    ...   def session_lacks(self, key):
    ...     print 'Lacks: %(key)s' % dict(key=key)
    >>> this = InSessionVerifier()
    >>> this.add_subscriber(Subscriber())

    >>> this.perform({'token': '1234'}, 'token')
    Contains: token=1234

    >>> this.perform({}, 'token')
    Lacks: token
    """

    def perform(self, session, key):
        """Checks if ``key`` is already contained in ``session``.

        The method publish an 'session_contains' message in case the session
        already contains an item nemed ``key``, and a 'session_lacks' message
        otherwise.
        """
        if key in session:
            self.publish('session_contains', key, session[key])
        else:
            self.publish('session_lacks', key)


class CodeExtractor(Publisher):
    """
    >>> from collections import namedtuple
    >>> Params = namedtuple('Params', 'error code'.split())
    >>> class Subscriber(object):
    ...   def permission_denied(self):
    ...     print 'Permission denied'
    ...   def code_absent(self):
    ...     print 'Code not present'
    ...   def code_valid(self, code):
    ...     print 'Valid code: %(code)s' % dict(code=code)
    >>> this = CodeExtractor()
    >>> this.add_subscriber(Subscriber())

    >>> this.perform(Params('error message', None))
    Permission denied

    >>> this.perform(Params(None, None))
    Code not present

    >>> this.perform(Params(None, 'code'))
    Valid code: code
    """
    def perform(self, params):
        """Tries to extract the authorization token from the list of request
        params.

        On success the code is published within a 'code_valid' message.  If the
        user has denied permissions to the application a 'permission_denied'
        message is sent back to subscribers and finally if the code is not
        present, a 'code_absent' will be generated. 
        """
        if params.error:
            self.publish('permission_denied')
        elif params.code is None:
            self.publish('code_absent')
        else:
            self.publish('code_valid', params.code)


class OAuthInvoker(Publisher):
    """
    >>> from mock import MagicMock
    >>> from mock import Mock
    >>> class Subscriber(object):
    ...   def oauth_error(self, url, status, content):
    ...     print 'Error: %(url)s %(status)s %(content)s' % locals()
    ...   def oauth_success(self, url, content):
    ...     print 'Success: %(url)s %(content)s' % locals()
    >>> this = OAuthInvoker()
    >>> this.add_subscriber(Subscriber())

    >>> client = Mock(request=MagicMock(return_value=({'status': '404'}, None)))
    >>> this.perform(client, 'http://not.found.it')
    Error: http://not.found.it 404 None

    >>> client = Mock(request=MagicMock(return_value=({'status': '200'},
    ...                                 'Response content')))
    >>> this.perform(client, 'http://found.it')
    Success: http://found.it Response content
    """

    def perform(self, client, url):
        """Performs a request to the given ``url`` using the specified OAuth
        client ``client``.

        If the request completes successfully a 'success' message is published
        followed by the content of the response;  on the other end, if something
        goes wrong while trying to reach ``url``, an 'error' message is
        published togheter with the ``url``, the status of the request and its
        content.
        """
        (resp, content) = client.request(url, 'GET')
        if resp['status'] != '200':
            self.publish('oauth_error', url, resp['status'], content)
        else:
            self.publish('oauth_success', url, content)
