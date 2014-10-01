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

class UserWithFacebookIdGetter(Publisher):
    def perform(self, repository, facebook_id):
        user = repository.with_facebook_id(facebook_id)
        if user is None:
            self.publish('user_not_found', facebook_id)
        else:
            self.publish('user_found', user)


class UserWithAcsIdGetter(Publisher):
    def perform(self, repository, acs_id):
        user = repository.with_acs_id(acs_id)
        if user is None:
            self.publish('user_not_found', acs_id)
        else:
            self.publish('user_found', user)


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
    def perform(self, repository, acs_id, facebook_id, name, avatar, email,
                locale):
        user = repository.add(acs_id, facebook_id, name, avatar, email, locale)
        self.publish('user_created', user)


class UserUpdater(Publisher):
    def perform(self, user, acs_id, facebook_id, name, avatar, email, locale):
        user.acs_id = acs_id
        user.facebook_id = facebook_id
        user.name = name
        user.avatar = avatar
        user.email = email
        user.locale = locale
        self.publish('user_updated', user)


def serialize(user):
    if user is None:
        return None
    data = dict(id=user.id, name=user.name, avatar=user.avatar,
             locale=user.locale)
    if hasattr(user, 'stars'):
        data.update(stars=user.stars)
    if hasattr(user, 'received_rates'):
        data.update(received_rates=user.received_rates)
    return data


class UserSerializer(Publisher):
    def perform(self, user):
        self.publish('user_serialized', serialize(user))


def serialize_private(user):
    data = serialize(user)
    if hasattr(user, 'rides_given'):
        data.update(rides_given=user.rides_given)
    return data


class UserSerializerPrivate(Publisher):
    def perform(self, user):
        self.publish('user_serialized', serialize_private(user))


def enrich(rates_repository, user):
    user.stars = rates_repository.avg_stars(user.id)
    user.received_rates = rates_repository.received_rates(user.id)
    return user

def _enrich(rates_repository, user):
    return enrich(rates_repository, user)

class UserEnricher(Publisher):
    def perform(self, rates_repository, user):
        self.publish('user_enriched', _enrich(rates_repository, user))


def enrich_private(rates_repository, drive_requests_repository, user):
    user = enrich(rates_repository, user)
    user.rides_given = drive_requests_repository.rides_given(user.id)
    return user

def _enrich_private(rates_repository, drive_requests_repository, user):
    return enrich_private(rates_repository, drive_requests_repository, user)

class UserEnricherPrivate(Publisher):
    def perform(self, rates_repository, drive_requests_repository, user):
        self.publish('user_enriched', _enrich_private(rates_repository,
                                                      drive_requests_repository,
                                                      user))
