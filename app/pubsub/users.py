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

        When done, a 'account_refreshed' message will be published toghether
        with the refreshed record.
        """
        account = repository.refresh_account(userid, externalid, accounttype)
        self.publish('account_refreshed', account)


class TokenRefresher(Publisher):
    def perform(self, repository, userid):
        """Refreshes the token associated with user identified by ``userid``.

        When done, a 'token_refreshed' message will be published toghether
        with the refreshed record.
        """
        token = repository.refresh_token(userid)
        self.publish('token_refreshed', token)


class UserCreator(Publisher):
    def perform(self, repository, name, avatar):
        """Creates a new user with the specified set of properties.

        On success a 'user_created' message will be published toghether
        with the created user.
        """
        user = repository.add(name, avatar)
        self.publish('user_created', user)


def serialize(user):
    if user is None:
        return None
    return dict(id=user.id, name=user.name, avatar=user.avatar)


class UserSerializer(Publisher):
    def perform(self, user):
        """Convert the given user into a serializable dictionary.

        At the end of the operation the method will emit a
        'user_serialized' message containing the serialized object (i.e.
        user dictionary).
        """
        from app.pubsub.drivers import serialize as serialize_driver
        from app.pubsub.passengers import serialize as serialize_passenger
        d = serialize(user)
        d.update(driver=serialize_driver(user.driver))
        d.update(passenger=serialize_passenger(user.passenger))
        self.publish('user_serialized', d)
