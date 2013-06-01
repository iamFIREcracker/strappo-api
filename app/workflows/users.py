#!/usr/bin/env python
# -*- coding: utf-8 -*-

import app.forms.users as userforms
from app.pubsub.users import UserCreator
from app.weblib.forms import describe_invalid_form
from app.weblib.pubsub import FormValidator
from app.weblib.pubsub import Future
from app.weblib.pubsub import LoggingSubscriber


def add_user(logger, params, repository):
    logger = LoggingSubscriber(logger)
    formvalidator = FormValidator()
    usercreator = UserCreator()
    res = Future()

    class FormValidatorSubscriber(object):
        def invalid_form(self, errors):
            res.set((False, dict(success=False, errors=errors)))
        def valid_form(self, form):
            usercreator.perform(repository, form.d.name, form.d.phone,
                                form.d.avatar)

    class UserUpdaterSubscriber(object):
        def user_created(self, userid, name, phone, avatar):
            res.set((True, userid))

    formvalidator.add_subscriber(logger, FormValidatorSubscriber())
    usercreator.add_subscriber(logger, UserUpdaterSubscriber())
    formvalidator.perform(userforms.add(), params, describe_invalid_form)
    return res.get()
