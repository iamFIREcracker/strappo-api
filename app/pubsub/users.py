#!/usr/bin/env python
# -*- coding: utf-8 -*-


from app.weblib.pubsub import Publisher


class AlreadyRegisteredVerifier(Publisher):
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
    def perform(self, repository, userid, externalid, accounttype):
        """Refreshes the user external account.

        When done, a 'account_refreshed' message will be published followed by
        the ID of the new account
        """
        accountid = repository.refresh_account(userid, externalid, accounttype)
        self.publish('account_refreshed', accountid)


class TokenRefresher(Publisher):
    def perform(self, repository, userid):
        """Refreshes the token associated with user identified by ``userid``.

        When done, a 'token_refreshed' message will be published followed by
        the ID of the new token.
        """
        tokenid = repository.refresh_token(userid)
        self.publish('token_refreshed', tokenid)


class UserCreator(Publisher):
    def perform(self, repository, name, avatar):
        """Creates a new user with the specified set of properties.

        On success a 'user_created' message will be published, followed by
        the id of the new user and the user properties.
        """
        userid = repository.add(name, avatar)
        self.publish('user_created', userid, name, avatar)

