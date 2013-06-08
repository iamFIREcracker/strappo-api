#!/usr/bin/env python
# -*- coding: utf-8 -*-

import app.forms.users as user_forms
from app.pubsub.users import AccountRefresher
from app.pubsub.users import AlreadyRegisteredVerifier
from app.pubsub.users import TokenRefresher
from app.pubsub.users import UserCreator
from app.weblib.forms import describe_invalid_form
from app.weblib.pubsub import FormValidator
from app.weblib.pubsub import Future
from app.weblib.pubsub import LoggingSubscriber
from app.weblib.pubsub import Publisher
from app.weblib.pubsub.auth import InSessionVerifier


class LoginAuthorizedWorkflow(Publisher):
    """Defines a workflow managing the user post-authorization process."""

    def perform(self, orm, logger, session, session_key, params_extractor,
                repository, account_type):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        session_verifier = InSessionVerifier()
        already_registered = AlreadyRegisteredVerifier()
        form_validator = FormValidator()
        user_creator = UserCreator()
        account_refresher = AccountRefresher()
        token_refresher = TokenRefresher()
        params = Future()
        future_user_id = Future()

        class InSessionVerifierSubscriber(object):
            def session_lacks(self, key):
                outer.publish('not_authorized')
            def session_contains(self, key, value):
                params.set(params_extractor(value))
                already_registered.perform(repository, params.get().externalid,
                                           account_type)

        class AlreadyRegisteredVerifierSubscriber(object):
            def not_registered(self, external_id, account_type):
                form_validator.perform(user_forms.add(), params.get(),
                                       describe_invalid_form)
            def already_registered(self, user_id):
                future_user_id.set(user_id)
                token_refresher.perform(repository, user_id)

        class FormValidatorSubscriber(object):
            def invalid_form(self, errors):
                outer.publish('invalid_form',
                              dict(success=False, errors=errors))
            def valid_form(self, form):
                user_creator.perform(repository, form.d.name, form.d.avatar)

        class UserCreatorSubscriber(object):
            def user_created(self, user):
                orm.add(user)
                future_user_id.set(user.id)
                account_refresher.perform(repository, user.id,
                                          params.get().externalid, account_type)

        class AccountRefresherSubscriber(object):
            def account_refreshed(self, account):
                orm.add(account)
                token_refresher.perform(repository, future_user_id.get())

        class TokenRefresherSubscriber(object):
            def token_refreshed(self, token):
                orm.add(token)
                outer.publish('success', token)

        session_verifier.add_subscriber(logger, InSessionVerifierSubscriber())
        already_registered.add_subscriber(logger,
                                          AlreadyRegisteredVerifierSubscriber())
        form_validator.add_subscriber(logger, FormValidatorSubscriber())
        user_creator.add_subscriber(logger, UserCreatorSubscriber())
        account_refresher.add_subscriber(logger, AccountRefresherSubscriber())
        token_refresher.add_subscriber(logger, TokenRefresherSubscriber())
        session_verifier.perform(session, session_key)
