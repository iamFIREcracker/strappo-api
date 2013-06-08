#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc

import web


class AbstractCookieAuthorizableController(object):
    """
    >>> class Handler(AbstractCookieAuthorizableController):
    ...   def get_user(self, token):
    ...     return 'ok' if token == 'valid' else 'no'

    >>> web.cookies = lambda: dict()
    >>> this = Handler()
    >>> this.current_user
    'no'

    >>> web.cookies = lambda: dict(token='invalid')
    >>> this = Handler()
    >>> this.current_user
    'no'

    >>> web.cookies = lambda: dict(token='valid')
    >>> this = Handler()
    >>> this.current_user
    'ok'
    """
    __metaclass__ = abc.ABCMeta

    @property
    def current_user(self):
        if not hasattr(self, '_current_user'):
            userid = web.cookies().get('token')
            self._current_user = self.get_user(userid)
        return self._current_user

    @abc.abstractmethod
    def get_user(self, token):
        """Gets the user identified associated with ``token``."""
        pass


class AbstractParamAuthorizableController(object):
    """
    >>> class Handler(AbstractParamAuthorizableController):
    ...   def get_user(self, token):
    ...     return 'ok' if token == 'valid' else 'no'

    >>> web.input = lambda **kw: dict(**kw)
    >>> this = Handler()
    >>> this.current_user
    'no'

    >>> web.input = lambda **kw: dict(dict(**kw).items() +
    ...                               dict(token='invalid').items())
    >>> this = Handler()
    >>> this.current_user
    'no'

    >>> web.input = lambda **kw: dict(dict(**kw).items() +
    ...                               dict(token='valid').items())
    >>> this = Handler()
    >>> this.current_user
    'ok'
    """
    __metaclass__ = abc.ABCMeta

    @property
    def current_user(self):
        if not hasattr(self, '_current_user'):
            userid = web.input(token=None).get('token')
            self._current_user = self.get_user(userid)
        return self._current_user

    @abc.abstractmethod
    def get_user(self, token):
        """Gets the user identified associated with ``token``."""
        pass
