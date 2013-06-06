#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

import web
from web.utils import storage

from app.controllers import CookieAuthorizedController
from app.repositories.users import UsersRepository
from app.workflows.users import LoginAuthorizedWorkflow
from app.weblib.pubsub import LoggingSubscriber


class LoginFakeAuthorizedController(CookieAuthorizedController):
    def GET(self):
        logger = LoggingSubscriber(web.ctx.logger)
        login_authorized = LoginAuthorizedWorkflow()

        def paramsextractor(token):
            return storage(externalid=unicode(uuid.uuid4()), name='John Smith',
                           phone='+123 345346',
                           avatar='http://www.placehold.it/128x128/EFEFEF/AAAAAA&text=no+image')

        class LoginAuthorizedSubscriber(object):
            def not_authorized(self):
                raise web.unauthorized()
            def invalid_form(self, errors):
                web.ctx.session.pop('fake_access_token')
                raise web.internalerror()
            def token_created(self, token_id):
                web.ctx.session.pop('fake_access_token')
                web.ctx.orm.commit()
                web.setcookie('token', token_id) # XXX expiration date
                raise web.found('/profile')

        login_authorized.add_subscriber(logger, LoginAuthorizedSubscriber())
        login_authorized.perform(web.ctx.logger, web.ctx.session,
                                 'fake_access_token', paramsextractor,
                                 UsersRepository, 'facebook')
