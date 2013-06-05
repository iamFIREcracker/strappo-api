#!/usr/bin/env python
# -*- coding: utf-8 -*-


from app.weblib.pubsub import Publisher


class AlreadyRegisteredVerifier(Publisher):
    """
    >>> from mock import MagicMock
    >>> from mock import Mock
    >>> class Subscriber(object):
    ...   def already_registered(self, userid):
    ...     print 'Already registered: %(userid)s' % locals()
    ...   def not_registered(self, externalid, account):
    ...     print 'Not registered: %(externalid)s, %(account)s' % locals()
    >>> this = AlreadyRegisteredVerifier()
    >>> this.add_subscriber(Subscriber())

    >>> repo = Mock(with_account=MagicMock(return_value=None))
    >>> this.perform(repo, 'wrong_external_id', 'facebook')
    Not registered: wrong_external_id, facebook

    >>> repo = Mock(with_account=MagicMock(return_value=Mock(id='uid')))
    >>> this.perform(repo, 'existing_id', 'twitter')
    Already registered: uid
    """

    def perform(self, repository, externalid, accounttype):
        """Checks whether a user identified by the given ID has already an
        associated external account of the specified type.

        Generates an 'already_registered' message followed by the ID of the
        registered user if a user with the specified account already extist.
        Otherwise a 'not_registered' message together with the external id and
        account type.
        """
        user = repository.with_account(externalid, accounttype)
        if user is not None:
            self.publish('already_registered', user.id)
        else:
            self.publish('not_registered', externalid, accounttype)


class AccountRefresher(Publisher):
    """
    >>> from mock import MagicMock
    >>> from mock import Mock
    >>> class Subscriber(object):
    ...   def account_refreshed(self, accountid):
    ...     print 'Account refreshed: %(accountid)s' % locals()
    >>> this = AccountRefresher()
    >>> this.add_subscriber(Subscriber())

    >>> repo = Mock(refresh_account=MagicMock(return_value='account_id'))
    >>> this.perform(repo, 'user_id', 'external_id', 'facebook')
    Account refreshed: account_id
    """

    def perform(self, repository, userid, externalid, accounttype):
        """Refreshes the user external account.

        When done, a 'account_refreshed' message will be published followed by
        the ID of the new account
        """
        accountid = repository.refresh_account(userid, externalid, accounttype)
        self.publish('account_refreshed', accountid)


class TokenRefresher(Publisher):
    """
    >>> from mock import MagicMock
    >>> from mock import Mock
    >>> class Subscriber(object):
    ...   def token_refreshed(self, tokenid):
    ...     print 'Token refreshed: %(tokenid)s' % locals()
    >>> this = TokenRefresher()
    >>> this.add_subscriber(Subscriber())

    >>> repo = Mock(refresh_token=MagicMock(return_value='token_id'))
    >>> this.perform(repo, 'user_id')
    Token refreshed: token_id
    """

    def perform(self, repository, userid):
        """Refreshes the token associated with user identified by ``userid``.

        When done, a 'token_refreshed' message will be published followed by
        the ID of the new token.
        """
        tokenid = repository.refresh_token(userid)
        self.publish('token_refreshed', tokenid)


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

