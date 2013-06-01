#!/usr/bin/env python
# -*- coding: utf-8 -*-


from app.weblib.pubsub import Publisher


class UserCreator(Publisher):
    """
    >>> from mock import MagicMock
    >>> from mock import Mock
    >>> class Subscriber(object):
    ...   def user_created(self, userid, name, phone, avatar):
    ...     msg = 'User created: %(id)s %(name)s %(phone)s %(avatar)s'
    ...     msg = msg % dict(id=userid, name=name, phone=phone, avatar=avatar)
    ...     print msg
    >>> this = UserCreator()
    >>> this.add_subscriber(Subscriber())
    >>> repo = Mock(add=MagicMock(return_value='new_id'))

    >>> this.perform(repo, 'John Smith', '+13 3253465', 'http://avatar.com/me')
    User created: new_id John Smith +13 3253465 http://avatar.com/me
    """

    def perform(self, repository, name, phone, avatar):
        """Creates a new user with the specified set of properties.

        On success a 'user_created' message will be published, followed by
        the id of the new user and the user properties.
        """
        userid = repository.add(name, phone, avatar)
        self.publish('user_created', userid, name, phone, avatar)

