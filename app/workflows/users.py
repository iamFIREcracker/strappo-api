#!/usr/bin/env python
# -*- coding: utf-8 -*-

import app.forms.users as userforms
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

    def perform(self, logger, session, sessionkey, paramsextractor,
                repository, account_type):
        outer = self # Handy to access ``self`` from inner classes
        logger = LoggingSubscriber(logger)
        sessionverifier = InSessionVerifier()
        alreadyregistered = AlreadyRegisteredVerifier()
        formvalidator = FormValidator()
        usercreator = UserCreator()
        accountrefresher = AccountRefresher()
        tokenrefresher = TokenRefresher()
        params = Future()
        future_userid = Future()

        class InSessionVerifierSubscriber(object):
            def session_lacks(self, key):
                outer.publish('not_authorized')
            def session_contains(self, key, value):
                params.set(paramsextractor(value))
                alreadyregistered.perform(repository, params.get().externalid,
                                          account_type)

        class AlreadyRegisteredVerifierSubscriber(object):
            def not_registered(self, externalid, account_type):
                formvalidator.perform(userforms.add(), params.get(),
                                      describe_invalid_form)
            def already_registered(self, userid):
                future_userid.set(userid)
                tokenrefresher.perform(repository, userid)

        class FormValidatorSubscriber(object):
            def invalid_form(self, errors):
                outer.publish('invalid_form',
                              dict(success=False, errors=errors))
            def valid_form(self, form):
                usercreator.perform(repository, form.d.name, form.d.avatar)

        class UserCreatorSubscriber(object):
            def user_created(self, userid, name, avatar):
                future_userid.set(userid)
                accountrefresher.perform(repository, userid,
                                         params.get().externalid, account_type)

        class AccountRefresherSubscriber(object):
            def account_refreshed(self, accountid):
                tokenrefresher.perform(repository, future_userid.get())

        class TokenRefresherSubscriber(object):
            def token_refreshed(self, tokenid):
                outer.publish('token_created', tokenid)

        sessionverifier.add_subscriber(logger, InSessionVerifierSubscriber())
        alreadyregistered.add_subscriber(logger,
                                         AlreadyRegisteredVerifierSubscriber())
        formvalidator.add_subscriber(logger, FormValidatorSubscriber())
        usercreator.add_subscriber(logger, UserCreatorSubscriber())
        accountrefresher.add_subscriber(logger, AccountRefresherSubscriber())
        tokenrefresher.add_subscriber(logger, TokenRefresherSubscriber())
        sessionverifier.perform(session, sessionkey)
