#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web.utils import storage

import app.forms.users as user_forms
from app.pubsub.users import TokenRefresher
from app.pubsub.users import TokenSerializer
from app.pubsub.users import UserCreator
from app.pubsub.users import UserEnricherPrivate
from app.pubsub.users import UserUpdater
from app.pubsub.users import UserWithIdGetter
from app.pubsub.users import UserWithFacebookIdGetter
from app.pubsub.users import UserWithAcsIdGetter
from app.pubsub.users import UserSerializerPrivate
from app.weblib.forms import describe_invalid_form
from app.weblib.pubsub import FacebookProfileGetter
from app.weblib.pubsub import FormValidator
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.pubsub import Publisher
from app.weblib.pubsub import Future



class ViewUserWorkflow(Publisher):
    """Defines a workflow to view the details of an active user."""

    def perform(self, logger, users_repository, user_id, rates_repository,
                drive_requests_repository, perks_repository,
                payments_repository):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        user_getter = UserWithIdGetter()
        user_enricher = UserEnricherPrivate()
        user_serializer = UserSerializerPrivate()

        class UserGetterSubscriber(object):
            def user_not_found(self, user_id):
                outer.publish('not_found', user_id)
            def user_found(self, user):
                user_enricher.perform(rates_repository,
                                      drive_requests_repository,
                                      perks_repository,
                                      payments_repository,
                                      user)

        class UserEnricherSubscriber(object):
            def user_enriched(self, user):
                user_serializer.perform(user)

        class UsersSerializerSubscriber(object):
            def user_serialized(self, blob):
                outer.publish('success', blob)

        user_getter.add_subscriber(logger, UserGetterSubscriber())
        user_enricher.add_subscriber(logger, UserEnricherSubscriber())
        user_serializer.add_subscriber(logger,
                                            UsersSerializerSubscriber())
        user_getter.perform(users_repository, user_id)


class LoginUserWorkflow(Publisher):
    """Defines a workflow managing the user login process."""

    def perform(self, orm, logger, repository, acs_id, facebook_adapter,
                facebook_token, locale):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        profile_getter = FacebookProfileGetter()
        form_validator = FormValidator()
        user_with_facebook_id_getter = UserWithFacebookIdGetter()
        user_with_acs_id_getter = UserWithAcsIdGetter()
        user_creator = UserCreator()
        user_updater = UserUpdater()
        token_refresher = TokenRefresher()
        token_serializer = TokenSerializer()
        form_future = Future()
        user_future = Future()

        class ProfileGetterSubscriber(object):
            def profile_not_found(self, error):
                outer.publish('internal_error')
            def profile_found(self, profile):
                params = storage(acs_id=acs_id,
                                 facebook_id=profile['id'],
                                 name=profile['name'],
                                 avatar=profile['avatar'],
                                 email=profile['email'],
                                 locale=locale)
                form_validator.perform(user_forms.add(), params,
                                       describe_invalid_form)

        class FormValidatorSubscriber(object):
            def invalid_form(self, errors):
                outer.publish('invalid_form',
                              dict(success=False, errors=errors))
            def valid_form(self, form):
                form_future.set(form)
                user_with_facebook_id_getter.perform(repository, form.d.facebook_id)

        class UserWithFacebookIdGetterSubscriber(object):
            def user_found(self, user):
                form = form_future.get()
                user_updater.perform(user, form.d.acs_id,
                                     form.d.facebook_id, form.d.name,
                                     form.d.avatar, form.d.email,
                                     form.d.locale)
            def user_not_found(self, facebook_id):
                form = form_future.get()
                user_with_acs_id_getter.perform(repository, form.d.acs_id)

        class UserWithAcsIdGetterSubscriber(object):
            def user_found(self, user):
                form = form_future.get()
                user_updater.perform(user, form.d.acs_id,
                                     form.d.facebook_id, form.d.name,
                                     form.d.avatar, form.d.email,
                                     form.d.locale)
            def user_not_found(self, acs_id):
                form = form_future.get()
                user_creator.perform(repository, form.d.acs_id,
                                     form.d.facebook_id, form.d.name,
                                     form.d.avatar, form.d.email,
                                     form.d.locale)

        class UserCreatorSubscriber(object):
            def user_created(self, user):
                orm.add(user)
                user_future.set(user)
                token_refresher.perform(repository, user.id)

        class UserUpdaterSubscriber(object):
            def user_updated(self, user):
                orm.add(user)
                user_future.set(user)
                token_refresher.perform(repository, user.id)

        class TokenRefresherSubscriber(object):
            def token_refreshed(self, token):
                orm.add(token)
                token_serializer.perform(token)

        class TokenSerializerSubscriber(object):
            def token_serialized(self, blob):
                outer.publish('success', blob, user_future.get())

        profile_getter.add_subscriber(logger, ProfileGetterSubscriber())
        form_validator.add_subscriber(logger, FormValidatorSubscriber())
        user_with_facebook_id_getter.\
            add_subscriber(logger, UserWithFacebookIdGetterSubscriber())
        user_with_acs_id_getter.\
            add_subscriber(logger, UserWithAcsIdGetterSubscriber())
        user_creator.add_subscriber(logger, UserCreatorSubscriber())
        user_updater.add_subscriber(logger, UserUpdaterSubscriber())
        token_refresher.add_subscriber(logger, TokenRefresherSubscriber())
        token_serializer.add_subscriber(logger, TokenSerializerSubscriber())
        profile_getter.perform(facebook_adapter, facebook_token)
