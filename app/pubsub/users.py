#!/usr/bin/env python
# -*- coding: utf-8 -*-


from app.weblib.pubsub import Publisher


class AlreadyRegisteredVerifier(Publisher):
    """
    >>> from mock import MagicMock
    >>> from mock import Mock
    >>> class Subscriber(object):
    ...   def already_registered(self, externalid, account):
    ...     print 'Already registered: %(externalid)s %(account)s' % locals()
    ...   def not_registered(self, externalid, account):
    ...     print 'Not registered: %(externalid)s %(account)s' % locals()
    >>> this = AlreadyRegisteredVerifier()
    >>> this.add_subscriber(Subscriber())

    >>> repo = Mock(with_account=MagicMock(return_value=None))
    >>> this.perform(repo, 'not_existing', 'facebook')
    Not registered: not_existing facebook

    >>> repo = Mock()
    >>> this.perform(repo, 'existing', 'twitter')
    Already registered: existing twitter
    """

    def perform(self, repository, externalid, accounttype):
        """Checks whether a user identified by the given ID has already an
        associated external account of the specified type.

        Generates an 'already_registered' message followed by the registered
        user, if a user with the specified account already extist.  Otherwise
        a 'not_registered' message together with the external id and account
        type.
        """
        if repository.with_account(externalid, accounttype) is not None:
            self.publish('already_registered', externalid, accounttype)
        else:
            self.publish('not_registered', externalid, accounttype)


class TokenRefresher(Publisher):
    """
    >>> from mock import MagicMock
    >>> from mock import Mock
    >>> class Subscriber(object):
    ...   def token_refreshed(self, tokenid, externalid, account):
    ...     msg = 'Token refreshed: %(tokenid)s %(externalid)s %(account)s'
    ...     print msg % locals()
    >>> this = TokenRefresher()
    >>> this.add_subscriber(Subscriber())

    >>> repo = Mock(refresh_account=MagicMock(return_value='token_id'))
    >>> this.perform(repo, 'external_id', 'facebook')
    Token refreshed: token_id external_id facebook
    """

    def perform(self, repository, externalid, accounttype):
        """Refreshes the token associated with the external account.

        When done, a 'token_refreshed' message will be published followed by
        the ID of the new token.
        """
        tokenid = repository.refresh_account(externalid, accounttype)
        self.publish('token_refreshed', tokenid, externalid, accounttype)


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

