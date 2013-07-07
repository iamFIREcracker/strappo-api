#!/usr/bin/env python
# -*- coding: utf-8 -*-


from app.weblib.pubsub import Publisher


class UserWithIdGetter(Publisher):
    def perform(self, repository, user_id):
        """Get the user identified by ``user_id``.

        If such user exists, a 'user_found' message is published containing the
        user details;  on the other hand, if no user exists with the specified
        ID, a 'user_not_found' message will be published
        """
        user = repository.get(user_id)
        if user is None:
            self.publish('user_not_found', user_id)
        else:
            self.publish('user_found', user)


class AlreadyRegisteredVerifier(Publisher):
    def perform(self, repository, acs_id):
        """Checks whether the system already contains a user with the specified
        ACS ID.

        Generates an 'already_registered' message followed by the ID of the
        registered user if a user with the specified ACS ID already extists.
        Otherwise a 'not_registered' message together with the ACS ID.
        """
        user = repository.with_acs_id(acs_id)
        if user is not None:
            self.publish('already_registered', user.id)
        else:
            self.publish('not_registered', acs_id)


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


class TokenSerializer(Publisher):
    def perform(self, token):
        """Convert the given token into a serializable dictionary.

        At the end of the operation the method will emit a
        'token_serialized' message containing the serialized object (i.e.
        token dictionary).
        """
        self.publish('token_serialized', dict(id=token.id,
                                              user_id=token.user_id))


class UserCreator(Publisher):
    def perform(self, repository, acs_id, name, avatar):
        """Creates a new user with the specified set of properties.

        On success a 'user_created' message will be published toghether
        with the created user.
        """
        user = repository.add(acs_id, name, avatar)
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
