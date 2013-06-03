#!/usr/bin/env python
# -*- coding: utf-8 -*-

import app.forms.users as userforms
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

    def perform(self, logger, session, sessionkey, paramsextractor,
                repository, account):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        sessionverifier = InSessionVerifier()
        alreadyregistered = AlreadyRegisteredVerifier()
        formvalidator = FormValidator()
        usercreator = UserCreator()
        tokenrefresher = TokenRefresher()
        params = Future()

        class InSessionVerifierSubscriber(object):
            def session_lacks(self, key):
                outer.publish('not_authorized')
            def session_contains(self, key, value):
                params.set(paramsextractor(value))
                alreadyregistered.perform(repository, params.get().externalid,
                                          account)

        class AlreadyRegisteredVerifierSubscriber(object):
            def not_registered(self, externalid, account):
                formvalidator.perform(userforms.add(), params.get(),
                                      describe_invalid_form)
            def already_registered(self, externalid, account):
                tokenrefresher.perform(repository, externalid, account)

        class FormValidatorSubscriber(object):
            def invalid_form(self, errors):
                outer.publish('invalid_form',
                              dict(success=False, errors=errors))
            def valid_form(self, form):
                usercreator.perform(repository, form.d.name, form.d.phone,
                                    form.d.avatar)

        class UserCreatorSubscriber(object):
            def user_created(self, userid, name, phone, avatar):
                tokenrefresher.perform(repository, params.get().externalid,
                                       account)

        class TokenRefresherSubscriber(object):
            def token_refreshed(self, tokenid, externalid, account):
                outer.publish('token_created', tokenid)

        sessionverifier.add_subscriber(logger, InSessionVerifierSubscriber())
        alreadyregistered.add_subscriber(logger,
                                         AlreadyRegisteredVerifierSubscriber())
        tokenrefresher.add_subscriber(logger, TokenRefresherSubscriber())
        formvalidator.add_subscriber(logger, FormValidatorSubscriber())
        usercreator.add_subscriber(logger, UserCreatorSubscriber())
        sessionverifier.perform(session, sessionkey)
