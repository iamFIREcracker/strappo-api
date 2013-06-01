#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc

import web


class AbstractCookieAuthorizedController(object):
    """
    >>> class Handler(AbstractCookieAuthorizedController):
    ...   def get_user(self, userid):
    ...     return 'ok' if userid == 'valid' else 'no'

    >>> web.cookies = lambda: dict()
    >>> this = Handler()
    >>> this.current_user
    'no'

    >>> web.cookies = lambda: dict(userid='valid')
    >>> this = Handler()
    >>> this.current_user
    'ok'
    """
    __metaclass__ = abc.ABCMeta

    @property
    def current_user(self):
        if not hasattr(self, '_current_user'):
            userid = web.cookies().get('userid')
            self._current_user = self.get_user(userid)
        return self._current_user

    @abc.abstractmethod
    def get_user(self, userid):
        """Gets the user identified by ``userid`` or None otherwise."""
        pass
